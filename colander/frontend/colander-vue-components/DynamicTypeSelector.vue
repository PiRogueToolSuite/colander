<script setup>
</script>
<script>
export default {
  data() {
    return {
      raw: {super_types:[], types:{}},
      initialModel: 'OBSERVABLE',
      initialType: 'IPV4',
      selectedModel: 'OBSERVABLE',
      selectedType: 'IPV4',
      resetToModel: null,
    };
  },
  mounted() {

  },
  created() {
    this.$cache.retrieve('creatable_entities').then((modelsData)=>{
      this.raw = modelsData
      this.initializeAgainstQueryUrl();
    });
  },
  computed: {
    modelNames() {
      return this.raw.super_types;
    },
    modelTypes() {
      if (this.selectedModel in this.raw.types)
        return this.raw.types[this.selectedModel];
      else
        return [];
    },
  },
  methods: {
    initializeAgainstQueryUrl() {
      try {
        let queryString = window.location.search;
        let urlParams = new URLSearchParams(queryString);
        let querySuperType = urlParams.get('super_type');
        let queryType = urlParams.get('type');

        if (querySuperType && queryType) {
          // 'super_type' and 'type' are available in query string
          let superTypes = this.raw.super_types;
          if (superTypes.filter((st) => st.short_name === querySuperType).length > 0) {
            let types = this.raw.types[querySuperType];
            if (types.filter((t) => t.id === queryType).length > 0) {
              // Both 'super_type' and 'type' exists in 'database'
              // let initialize with that
              this.initialModel = querySuperType;
              this.initialType = queryType;
            } else {
              console.warn(`Can't find '${queryType}' type in '${querySuperType}' super type`);
            }
          } else {
            console.warn(`Can't find '${querySuperType}' super type`);
          }
        }
      } catch(err) {
        console.error(`Can't parse query string`, err);
      }
      this.selectedModel = this.initialModel;
      this.selectedType = this.initialType;
    },
    resetSelectedType(e) {
      this.resetToModel = e;
    },
  },
};
</script>
<template>
  <div class="col">
    <h4>Entity</h4>
    <select
      v-model="selectedModel"
      id="id_super_type_selector"
      size="6"
      required
      class="form-select"
      name="super_type">
      <option v-for="option in modelNames" :value="option.short_name">{{option.name}}</option>
    </select>
  </div>
  <div class="col">
    <h4>Type</h4>
    <select
      v-model="selectedType"
      size="6"
      id="id_type_selector"
      required
      name="type"
      class="form-select">
      <option v-for="option in modelTypes" :value="option.id">{{option.name}}</option>
    </select>
  </div>
</template>
<style>

</style>
