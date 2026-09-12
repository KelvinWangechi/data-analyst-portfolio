import {pathToFileURL} from 'node:url';
// Normalize Windows paths passed to ESM imports by the webR worker.
export async function resolve(specifier, context, nextResolve) {
  if (/^[A-Za-z]:[\\/]/.test(specifier)) specifier=pathToFileURL(specifier).href;
  return nextResolve(specifier,context);
}
