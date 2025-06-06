
export const LogLevel = {
  NONE: 0,
  ERROR: 1,
  WARN: 2,
  INFO: 3,
  FIXME: 4,
  TODO: 5,
  DEBUG: 6,
};

const _log_entry = (currentLogLevel, msgLogLevel,
                    nativeTarget, ...msgArgs) => {
  if (msgLogLevel > currentLogLevel()) return;
  nativeTarget(...msgArgs);
};

export default {
  install(app, options) {
    app.config.globalProperties.$logLevel = options?.logLevel ?? LogLevel.INFO;
    app.config.globalProperties.$logger = (component, componentName) => {
      component.$debug = _log_entry.bind(
        component,
        ()=>app.config.globalProperties.$logLevel,
        LogLevel.DEBUG,
        console.debug.bind(console,'[DEBUG]', `${componentName}:`),
      );
      component.$todo = _log_entry.bind(
        component,
        ()=>app.config.globalProperties.$logLevel,
        LogLevel.TODO,
        console.info.bind(console,'[TODO ]', `${componentName}:`),
      );
      component.$fixme = _log_entry.bind(
        component,
        ()=>app.config.globalProperties.$logLevel,
        LogLevel.FIXME,
        console.warn.bind(console,'[FIXME]', `${componentName}:`),
      );
      component.$info = _log_entry.bind(
        component,
        ()=>app.config.globalProperties.$logLevel,
        LogLevel.INFO,
        console.info.bind(console,'[INFO]', `${componentName}:`),
      );
      component.$warn = _log_entry.bind(
        component,
        ()=>app.config.globalProperties.$logLevel,
        LogLevel.WARN,
        console.warn.bind(console,'[WARN]', `${componentName}:`),
      );
      component.$error = _log_entry.bind(
        component,
        ()=>app.config.globalProperties.$logLevel,
        LogLevel.ERROR,
        console.error.bind(console,'[ERROR]', `${componentName}:`),
      );
    };
  }
};
