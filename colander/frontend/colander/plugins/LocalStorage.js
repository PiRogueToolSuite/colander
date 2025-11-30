class LocalStorage {
  static DEFAULT_OPTIONS = Object.freeze({ prefix: 'colander' });

  options
  constructor(options) {
    this.options = Object.assign({}, LocalStorage.DEFAULT_OPTIONS, options);
  }
  _key(subKey) {
    return `${this.options.prefix}.${subKey}`;
  }
  get(key, _default) {
    _default ??= "";
    let _stored = localStorage.getItem(this._key(key));
    if (_stored) return JSON.parse(_stored);
    return _default;
  }
  set(key, value) {
    localStorage.setItem(this._key(key), JSON.stringify(value));
  }
}

export default {
  install(app, options) {
    app.config.globalProperties.$localStorage = new LocalStorage(options);
  }
};
