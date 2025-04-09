<script>
export default {
  props: {
    dataType: String,
  },
  data() {
    return {
      textArea: null,
      entity_types: {},
      storedAttributes: [],
      dataLoaded: false,
    };
  },
  created() {
    this.$logger(this, 'HStoreTable');
    // Retrieve all artifact types
    this.$cache.retrieve('entity_types').then((ats) => {
      if (this.dataType) {
        this.entity_types = ats[this.dataType];
      }
      else {
        this.$info('HStoreTable', `No 'dataType' set`);
      }
    });
  },
  mounted() {
    this.textArea = $('textarea#id_attributes');
    $('textarea#id_attributes').css('visibility', 'hidden');
    $('textarea#id_attributes').css('position', 'absolute');
    // Auto connect to type selector:
    let localTypeSelector = $('input[type=radio][name="type"]');
    if (localTypeSelector.length > 0) {
      $('input[type=radio][name="type"]').on('click', this.legacy_on_type_selection_changed);
    }
    else {
      this.$info('no local selector found');
    }

    this.$bus.on('entity-type-changed', this.nativeTypeChanged)
  },
  methods: {
    toto(event) {
      console.log('toto', event);
    },
    update_key(index, event) {
      const newKey = event.target.value;
      if (newKey.length > 0) {
        this.storedAttributes[index] = {key: newKey, value: this.storedAttributes[index].value};
      }
      this.update_json();
    },
    update_value(index, event) {
      const newValue = event.target.value;
      if (newValue.length > 0) {
        this.storedAttributes[index] = {key: this.storedAttributes[index].key, value: newValue};
      }
      this.update_json();
    },
    delete_attribute(index, event){
      this.storedAttributes.splice(index, 1);
      this.update_json();
    },
    add_attribute() {
      this.storedAttributes.push({key: 'new_key', value: ''});
    },
    nativeTypeChanged(entityType) {
      this.$debug('nativeTypeChanged', entityType);
      this.$debug('entity_types', this.entity_types);
      if (!this.entity_types) return;
      const default_attributes = this.entity_types[entityType].default_attributes;
      this.dataLoaded = false; // Reload from textarea
      this.attributes; // Accessing computed attributes, force refresh ?
                       // while $forceUpdate does not do its job ... o_Ô
      for (let k in default_attributes) {
        if (!this._is_key_stored(k)) {
          this.storedAttributes.push({key: k, value: default_attributes[k]});
        }
      }
    },
    legacy_on_type_selection_changed(e) {
      this.nativeTypeChanged(e.target.value);
    },
    _is_key_stored(k) {
      for (let i in this.storedAttributes) {
        if (this.storedAttributes[i].key === k) {
          return true
        }
      }
      return false;
    },
    update_json(){
      let obj = {};
      for (let i in this.storedAttributes){
        if (this.storedAttributes[i].value)
          obj[this.storedAttributes[i].key] = this.storedAttributes[i].value;
      }
      try {
        this.textArea.val(JSON.stringify(obj));
      } catch (TypeError){}
    }
  },
  computed: {
    attributes() {
      if (!this.dataLoaded) {
        this.storedAttributes = [];
        if (this.textArea) {
          let attr_from_textarea = this.textArea.val();
          if (attr_from_textarea.length > 1) {
            try {
              const attrs = JSON.parse(attr_from_textarea);
              let i = 0;
              for (let k in attrs) {
                this.storedAttributes.push({key: k, value: attrs[k]});
              }
            } catch (SyntaxError) {
            }
          }
          this.dataLoaded = true;
        }
      }
      return this.storedAttributes;
    }
  },
};
</script>
<template>
  <div class="mb-2">
    <div ref="slotContent" class="hidden">
      <slot/>
    </div>
    <div class="body attributes-form">
      <div class="input-group mb-1" v-for="(a, index) in attributes" :key="index">
        <input type="text" class="form-control" placeholder="Key" aria-label="Key"
               v-on:keyup="update_key(index, $event)"
               v-model="attributes[index].key">
        <span class="input-group-text">=</span>
        <input type="text" class="form-control" placeholder="Value" aria-label="Value"
               v-on:keyup="update_value(index, $event)"
               v-model="attributes[index].value">
        <a href="#" class="btn btn-outline-danger" v-on:click="delete_attribute(index, $event)"><i class="fa fa-trash"></i></a>
      </div>
      <a href="#" class="btn btn-sm btn-outline-primary" v-on:click="add_attribute($event)"><i class="fa fa-plus"></i></a>
    </div>
  </div>
</template>
<style lang="scss">
</style>
