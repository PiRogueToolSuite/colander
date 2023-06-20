# Webpack environment for Colander

These instructions are only needed if modification are made on frontend parts. 

## Initial setup

From root colander project folder, run :
```bash
npm install
```

## During development

In order to constantly compile frontend modifications, run :
```bash
npm run dev
```
This command use 'watch' file modification. Use SIG INT to get back to shell prompt.

If you need new dependency, use `npm install --save <dep>` as usual, and simply import it in your frontend source.

If you need to create a new separate frontend 'lib', add its entry point to `<colander root project>/webpack.config.js`.

## Before commit

It is preferable to commit a minified version of frontend files.
To do so, run :
```bash
npm run dist
```

