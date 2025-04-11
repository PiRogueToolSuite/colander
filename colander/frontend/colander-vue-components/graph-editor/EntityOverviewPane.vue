<script setup>
</script>
<script>
export default {
  data: () => ({
    entity: {},
    allStyles: {},
  }),
  methods: {
    date_str: (dStr) => {
      if (!dStr) return '';
      return new Intl.DateTimeFormat('default', {dateStyle: 'long', timeStyle: 'short'}).format(new Date(dStr));
    },
    close: function () {
      $(this.$el).trigger('close-component');
    },
    quickEdit: function () {
      $(this.$el).trigger('quick-edit-entity', [this.entity.id]);
    },
  },
  computed: {
    descriptionMarkdown: function() {
      // entity.description || 'No description'
      if (this.entity.description) {
        return Markdown.render(this.entity.description);
      }
      return 'No description';
    }
  }
};
</script>
<template>
  <div class="vue-component">
    <div class='vue-container container py-2'>
      <div class="body">
        <div class='mt-2 mb-2'><i class='fa fa-hashtag text-primary'></i> {{entity.id}}</div>
        <h3 class="text-truncate">
            <i v-bind:class="['fa', 'text-primary', allStyles[entity.super_type]?.['icon-font-classname']]" v-bind:title="entity.super_type"></i>
          {{entity.name}}
        </h3>
        <h4>Description</h4>
        <div class='mb-3' v-html="descriptionMarkdown"></div>
        <h4>Details</h4>
        <table class="mb-3">
            <tbody>
                <tr>
                    <td class="pe-1">TPL/PAP</td>
                    <td>{{entity.tlp}} / {{entity.pap}}</td>
                </tr>
                <tr>
                    <td class="pe-1">Type</td>
                    <td class="type-or-super-type" v-if="entity.type">
                      <i v-bind:class="['nf', 'text-primary', allStyles[entity.super_type]['types'][entity.type]?.['icon-font-classname']]" v-bind:title="entity.type"></i>
                      {{entity.type}}
                    </td>
                    <td class="type-or-super-type" v-else>
                      <i v-bind:class="['fa', 'text-primary', allStyles[entity.super_type]?.['icon-font-classname']]" v-bind:title="entity.super_type"></i>
                      {{entity.super_type}}
                    </td>
                </tr>
                <tr>
                    <td class="pe-1">Created at</td>
                    <td><i class='nf nf-fa-calendar text-primary'></i> {{date_str(entity.created_at)}}</td>
                </tr>
                <tr>
                    <td class="pe-1">Updated at</td>
                    <td><i class='nf nf-fa-calendar text-primary'></i> {{date_str(entity.updated_at)}}</td>
                </tr>
            </tbody>
        </table>
        <div v-if="entity.content">
          <h4>Content</h4>
          <pre class="bg-dark text-white rounded-2 p-2"><code>{{entity.content}}</code></pre>
        </div>
        <div v-if="entity.thumbnail_url">
          <h4>Thumbnail</h4>
          <img class="img-thumbnail" :src="entity.thumbnail_url" alt="{{entity.name}} thumbnail"/>
        </div>
      </div>
      <div class="footer">
        <button @click="close()" class="btn btn-outline-secondary me-1" type='button' role="close">Close</button>
        <a class="btn btn-primary me-1" :href="entity.absolute_url">Full details</a>
        <button @click="quickEdit()" class="btn btn-primary" type='button' role="edit">Quick edit</button>
      </div>
    </div>
  </div>
</template>
