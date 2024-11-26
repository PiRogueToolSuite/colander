export class Cache {
    #dictionary = {}
    constructor() {}
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
