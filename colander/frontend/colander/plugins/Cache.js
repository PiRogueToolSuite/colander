class Cache {
  #dictionary = {}
  constructor(options) {
    this.options = options;
  }
  async retrieve(domain) {
    if (domain in this.#dictionary) {
      return this.#dictionary[domain];
    }
    if (!(domain in this.options.dataSources))
      throw new Error(`retrieve error: ${domain} in not defined in cache dataSources`);
    let response = await fetch(this.options.dataSources[domain]);
    if (!response.ok) throw new Error(`retrieve error: unable to fetch domain:${domain} status:${response.status} msg:${response.statusText}`);
    this.#dictionary[domain] = await response.json();
    return this.#dictionary[domain];
  }
  store(domain, id, value) {
      this.#dictionary[domain] = this.#dictionary[domain] || {};
      return this.#dictionary[domain][id] = value;
  }
  contains(domain, id) {
      return (domain in this.#dictionary) && (id in this.#dictionary[domain]);
  }
  get(domain, id) {
      return this.#dictionary[domain]?.[id];
  }
}

export default {
  install(app, options) {
    app.config.globalProperties.$cache = new Cache(options);
  }
};
