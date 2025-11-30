class ThemeUtils {
  #theme = {}

  constructor(cache) {
    this.cache = cache;
    this.cache.retrieve('all_styles').then((styles) => {
      this.#theme = styles;
    });
  }

  async attachStyleToEntities(entities) {
    entities.forEach((entity) => {
      this.attachStyleToEntity(entity);
    })
  }

  async attachStyleToEntity(entity) {
    if (!Object.hasOwn(entity, 'superTypeStyle')) {
      entity.superTypeStyle = this.getSuperTypeStyle(entity);
      entity.type = this.getTypeStyle(entity);
    }
  }

  getSuperTypeStyle(entity) {
    return Object.values(this.#theme).find(
      (value) => value.short_name === entity.super_type.short_name
    );
  }

  getTypeStyle(entity) {
    const superTypeStyle = Object.values(this.#theme).find(
      (value) => value.short_name === entity.super_type.short_name
    );
    if (superTypeStyle) {
      return superTypeStyle.types[entity.type.short_name];
    }
  }
}

export default {
  install(app) {
    app.config.globalProperties.$themeUtils = new ThemeUtils(
      app.config.globalProperties.$cache
    );
  }
};
