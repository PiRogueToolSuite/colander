import EventEmitter from 'events';

export default {
  install(app, options) {
    app.config.globalProperties.$bus = new EventEmitter();
  }
};
