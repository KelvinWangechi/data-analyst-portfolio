# Base R analysis. Run from this directory with Rscript analysis.R.
# Browser export and SQLite aggregates are independently reconciled.
r <- read.csv('data/responses.csv', stringsAsFactors=FALSE, na.strings=NULL)
c <- read.csv('data/customers.csv', stringsAsFactors=FALSE)
a <- read.csv('data/assignments.csv', stringsAsFactors=FALSE)
i <- read.csv('data/invitations.csv', stringsAsFactors=FALSE)
stopifnot(!anyDuplicated(r$response_id), !anyDuplicated(c$customer_id))
r <- merge(r,c,by='customer_id',sort=FALSE)
r$has_text <- nchar(trimws(r$text)) > 0
issues <- a[a$sentiment == 'negative', ]
wilson <- function(k,n) {
  if(n==0) return(c(NA_real_,NA_real_))
  z <- qnorm(.975); p <- k/n; den <- 1+z^2/n
  center <- (p+z^2/(2*n))/den
  half <- z*sqrt(p*(1-p)/n+z^2/(4*n^2))/den
  c(max(0,center-half),min(1,center+half))
}
rows <- list()
for(group in c('All','Regular schedule','Changing schedule')) {
  eligible <- r[r$has_text & r$reason=='Too expensive' & (group=='All' | r$schedule==group), ]
  for(theme in unique(a$theme_id)) {
    n <- nrow(eligible)
    k <- length(intersect(unique(issues$response_id[issues$theme_id==theme]),eligible$response_id))
    interval <- wilson(k,n)
    rows[[length(rows)+1]] <- data.frame(segment=group,theme_id=theme,count=k,n=n,share=if(n>0) k/n else NA_real_,lower=interval[1],upper=interval[2])
  }
}
summary <- do.call(rbind,rows)
dir.create('results',showWarnings=FALSE)
write.csv(summary,'results/theme-summary.csv',row.names=FALSE)
invitations <- merge(i,c,by='customer_id')
response_rows <- lapply(unique(invitations$schedule),function(group) {
  x <- invitations[invitations$schedule==group,]
  data.frame(schedule=group,invited=nrow(x),responded=sum(x$responded),response_rate=mean(x$responded))
})
write.csv(do.call(rbind,response_rows),'results/response-rates.csv',row.names=FALSE)
price <- r[r$has_text & r$reason=='Too expensive',]
all <- summary[summary$segment=='All',]
afford <- all$count[all$theme_id=='affordability']
timing_ids <- unique(issues$response_id[issues$theme_id %in% c('pause_control','delivery_flexibility')])
timing <- length(intersect(price$response_id,timing_ids))
out <- data.frame(metric=c('responses','with_text','price_with_text','price_affordability','price_schedule'),value=c(nrow(r),sum(r$has_text),nrow(price),afford,timing))
write.csv(out,'results/r-summary.csv',row.names=FALSE)
writeLines(c(R.version.string,'Base R only. No contributed R packages required.'),'results/r-environment.txt')
print(out)
