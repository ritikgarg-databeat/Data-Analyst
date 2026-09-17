// `@types/plotly.js` only declares the package's main entry point — this
// re-exports the same types for the pre-bundled `dist/plotly-cartesian`
// subpath used by components/shared/plotly-view-inner.tsx (see that file's
// docstring for why that subpath is used instead of the main entry point).
declare module "plotly.js/dist/plotly-cartesian" {
  import Plotly from "plotly.js";
  export = Plotly;
}
