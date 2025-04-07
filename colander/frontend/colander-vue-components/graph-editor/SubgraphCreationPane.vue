<script setup>
</script>
<script>
export default {
  delimiters: ['[[', ']]'],
  data: () => ({
    allStyles: {},
    entities: {},
    subgraph: {},
  }),
  methods: {
    cancel: function () {
      $(this.$el).trigger('close-component');
    },
    save: function(edit_after_creation) {
      let tmp = JSON.parse(JSON.stringify(this.subgraph));
      $(this.$el).trigger('save-subgraph', [tmp, edit_after_creation]);
    },
  },
  computed: {
    invalidForm: function() {
      let name = this.subgraph.name?.trim();
      if (!name) return true;
      return false;
    },
    sortedEntities_keys: function() {
      if (!this.subgraph.overrides) return [];
      let keys = Object.keys(this.subgraph.overrides);
      return keys;
    },
  },
};
</script>
<template>
  <div class='vue-container container py-2'>
    <div class="body">
      <h5>
        <i class="nf text-primary nf-md-hubspot"></i>
        Sub Graph
      </h5>
      <div class="form-group mb-2">
        <label>Sub Graph name</label>
        <input class="form-control" type="text" placeholder="Sub Graph name" v-model="subgraph.name" name="name"/>
      </div>
      <div class="form-group mb-2">
        <label>Sub Graph description</label>
        <textarea class="form-control" type="text" placeholder="Sub Graph short description" v-model="subgraph.description" name="name"></textarea>
      </div>
      <div class="mb-2">
        <label>Sub Graph entities</label>
        <table class="table table-sm table-striped table-hover">
          <thead>
            <tr>
              <th scope="col" title="Entity type" width="1%">E</th>
              <th scope="col" title="Type" width="1%">T</th>
              <th >Name</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="eid in sortedEntities_keys">
              <td>
                <i v-bind:class="['fa', 'text-primary', 'actionable', allStyles[entities[eid].super_type]['icon-font-classname']]"
                   v-bind:title="entities[eid].super_type"></i>
              </td>
              <td>
                <i v-bind:class="['nf', 'text-primary', 'actionable', allStyles[entities[eid].super_type]['types'][entities[eid].type]?.['icon-font-classname']]"
                   v-bind:title="entities[eid].type"></i>
              </td>
              <td class='text-truncate'
                  style="max-width: 0;"
                  v-bind:title="entities[eid].name">[[ entities[eid].name ]]</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <div class="footer">
      <button @click="cancel()" type="button" class="btn btn-outline-secondary me-1" role="cancel">Cancel</button>
      <button @click="save(false)" v-bind:disabled="invalidForm" type="button" class="btn btn-primary me-1" role="save">Save</button>
      <button @click="save(true)" v-bind:disabled="invalidForm" type="button" class="btn btn-primary" role="save">Save and edit</button>
    </div>
  </div>
</template>
<style scoped>
</style>
