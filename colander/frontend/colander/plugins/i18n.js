class TranslationRegistry {
  #dictionary = {}

  constructor() {}

  translate(lang, refString, jsonFormatArgs) {
    jsonFormatArgs = jsonFormatArgs || {};

    this.#dictionary['en'] = this.#dictionary['en'] || {};
    this.#dictionary['en'][refString] = this.#dictionary['en'][refString] || refString;

    // Retrieve string to format
    let stringToFormat = refString;
    if (lang in this.#dictionary) {
      if (refString in this.#dictionary[lang]) {
        stringToFormat = this.#dictionary[lang][refString];
      }
    }

    // Format string
    const tokenRegex = /{(\w+)}/g; // tokenRegex is stateful
    let formattedString = stringToFormat;
    let match;
    while( (match = tokenRegex.exec(stringToFormat)) !== null ) {
      // Avoid infinite loops with zero-width matches
      if (match.index === tokenRegex.lastIndex) {
          tokenRegex.lastIndex++;
      }

      if (match[1] in jsonFormatArgs) {
        formattedString = formattedString.replaceAll(match[0], jsonFormatArgs[match[1]]);
      }
      else {
        console.warn(`Token:'${match[1]}' not found in format args to translate string:"${refString}"`);
      }
    }
    // Result
    return formattedString;
  }
}

export default {
  install(app, options) {
    const currentRegistry = new TranslationRegistry();
    app.config.globalProperties.$lang = 'en';
    app.config.globalProperties.$t = (referenceString, jsonFormatArguments) => {
      return currentRegistry.translate(
        app.config.globalProperties.$lang,
        referenceString,
        jsonFormatArguments
      );
    };
  }
};
