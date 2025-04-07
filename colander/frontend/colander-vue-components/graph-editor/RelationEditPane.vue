<script setup>
</script>
<script>
export default {
  delimiters: ['[[', ']]'],
  data: () => ({
    ctx: {},
    pending_edge: null,
    allStyles: {},
  }),
  methods: {
    cancel: function () {
      let tmp = JSON.parse(JSON.stringify(this.ctx));
      tmp.pending_edge = this.pending_edge;
      $(this.$el).trigger('close-component', [tmp]);
      this.pending_edge = null;
    },
    save: function() {
      let tmp = JSON.parse(JSON.stringify(this.ctx));
      tmp.pending_edge = this.pending_edge;
      this.pending_edge = null;
      $(this.$el).trigger('save-relation', [tmp]);
    },
    edit_relation: function(ctx) {
      let tmp = Object.assign({}, ctx);
      this.pending_edge = tmp.pending_edge;
      delete tmp.pending_edge;
      this.ctx = tmp;
      $(this.$el).find('input[name=name]').select();
    }
  },
  computed: {
    invalidForm: function() {
      let name = this.ctx.name?.trim();
      return !name;
    }
  }
};
</script>
<template>
  <div class='vue-container container py-2'>
    <div class="body">
      <h5>Entity relation</h5>
      <div class="form-group mb-2">
          <label>Relation name</label>
          <input class="form-control" type="text" placeholder="Relation name" v-model="ctx.name" name="name"/>
      </div>
    </div>
    <div class="footer">
        <button @click="cancel()" type="button" class="btn btn-outline-secondary me-1" role="cancel">Cancel</button>
        <button @click="save()" v-bind:disabled="invalidForm" type="button" class="btn btn-primary" role="save">Save</button>
    </div>
  </div>
</template>
<style scoped>
</style>
