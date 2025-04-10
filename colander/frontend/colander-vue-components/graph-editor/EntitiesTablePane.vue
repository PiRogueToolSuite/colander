<script setup>
</script>
<script>
export default {
  data() {
    return {
      entities: {},
      allStyles: {},
      overrides: {},
      editableVisibility: false,
      currentSort: {
        attributes: [], // defaults initial values set in created()
        direction: 'asc',
      },
      currentSearch: '',
    };
  },
  created() {
    this.$logger(this, 'EntitiesTablePane');
    this.$debug('created');
    // Globally defines sort attributes importance
    this.sortAttributesDefaults = [
      'name', 'visibility', 'super_type', 'type',
    ];
    this.currentSort.attributes = [...this.sortAttributesDefaults];
  },
  mounted() {
    this.$debug('mounted');
    this.$debug('$el', this.$el);
    $(this.$el).trigger('vue-ready',[$(this.$el), this]);
  },
  methods: {
    sort: function(attr) {
      if (attr === this.currentSort.attributes[0]) { // Unsafe ?
        this.currentSort.direction = this.currentSort.direction === 'asc' ? 'desc' : 'asc';
      }
      let newSortAttrs = [attr];
      for(let dfltAttr of this.sortAttributesDefaults) {
        if (newSortAttrs.includes(dfltAttr)) continue;
        newSortAttrs.push(dfltAttr);
      }
      this.currentSort.attributes = newSortAttrs;
    },
    isCurrentSort: function(attr) {
      return false;
    },
    focusEntity: function(eid) {
      $(this.$el).trigger('focus-entity', [eid]);
    },
    filterBy: function(filter) {
      let lcFilter = filter.toLowerCase();
      if (this.currentSearch.toLowerCase().includes(lcFilter)) return;
      this.currentSearch = lcFilter + " " + this.currentSearch;
    },
    track_new_entity: function(ctx) {
      // Not needed anymore

      // Despite Vue3's new Reactive architecture,
      // added entities do not refresh the table.
      // Even using $forceUpdate, settings initiale reactive(entities), etc)
      // The only hack found (for now) is to force a sort of the table
      this.sort(this.currentSort.attributes);
      this.$nextTick().then(() => {
        this.sort(this.currentSort.attributes);
      })
    },
    refresh: function() {
      // Used (at least) when an entity attributes is changed.
      this.$nextTick().then(() => {
        this.$forceUpdate();
      });
    },
    close: function () {
      this.$debug('Close entity');
      $(this.$el).trigger('close-component');
    },
    toggleEntityVisibility: function(eid) {
      this.overrides[eid] = this.overrides[eid] || {};
      this.overrides[eid].hidden = !(this.overrides[eid]?.hidden);
      $(this.$el).trigger('entity-visibility-changed', [eid, this.overrides[eid].hidden]);
    }
  },
  computed: {
    sortedEntities_keys: function() {
      let keys = Object.keys(this.entities);
      let query = this.currentSearch;
      query = query.replaceAll(/\s+/g, ' ');
      let searchREs = query.split(' ').map((s) => new RegExp(s, 'i') );
      keys = keys.filter((eid) => {
        for(let sre of searchREs) {
          let match =
                 sre.test(this.entities[eid].name)
              || sre.test(this.entities[eid].type)
              || sre.test(this.entities[eid].super_type);
          if (!match) return false;
        }
        return true;
      });
      keys.sort((aid,bid) => {
        let modifier = this.currentSort.direction === 'desc' ? -1 : 1;
        for(let currentAttr of this.currentSort.attributes) {
          if (currentAttr === 'visibility') {
            if (this.overrides[aid] === undefined || this.overrides[bid] === undefined) continue;
            if (this.overrides[aid]['hidden'] < this.overrides[bid]['hidden']) return -1 * modifier;
            if (this.overrides[aid]['hidden'] > this.overrides[bid]['hidden']) return 1 * modifier;
          } else {
            if (this.entities[aid][currentAttr] < this.entities[bid][currentAttr]) return -1 * modifier;
            if (this.entities[aid][currentAttr] > this.entities[bid][currentAttr]) return 1 * modifier;
          }
        }
        return 0;
      });
      return keys;
    }
  }
};
</script>
<template>
  <div class="vue-component">
    <div class='vue-container container py-2'>
      <div class="body">
        <input class='form-control' type="text" v-model="currentSearch" placeholder="Quick search for entities in this graph"/>
        <div class="table-sticky-head">
          <table class="table table-sm table-striped table-hover">
            <thead>
              <tr v-bind:class="[ 'sort-direction', currentSort.direction ]">
                <th @click="sort('super_type')"
                    v-bind:class="{ 'sort-attribute': true, 'sort-active': isCurrentSort('super_type') }"
                    scope="col" title="Entity type" width="1%">E</th>
                <th @click="sort('type')"
                    v-bind:class="{ 'sort-attribute': true, 'sort-active': isCurrentSort('type') }"
                    scope="col" title="Type" width="1%">T</th>
                <th @click="sort('name')"
                    v-bind:class="{ 'sort-attribute': true, 'sort-active': isCurrentSort('name') }"
                    scope="col">Name</th>
                <th @click="sort('visibility')"
                    v-bind:class="{ 'sort-attribute': true, 'sort-active': isCurrentSort('visibility') }"
                    scope="col" width="1%">
                  <i class='fa fa-filter'></i>
                </th>
              </tr>
            </thead>
            <tbody v-if="sortedEntities_keys.length > 0">
              <tr v-for="eid in sortedEntities_keys" v-bind:class="{ hidden: overrides[eid]?.hidden }">
                <td>
                  <i @click="filterBy(entities[eid].super_type)"
                     v-bind:class="['fa', 'text-primary', 'actionable', allStyles[entities[eid].super_type]['icon-font-classname']]"
                     v-bind:title="entities[eid].super_type"></i>
                </td>
                <td>
                  <i @click="filterBy(entities[eid].type)"
                     v-bind:class="['nf', 'text-primary', 'actionable', allStyles[entities[eid].super_type]['types'][entities[eid].type]?.['icon-font-classname']]"
                     v-bind:title="entities[eid].type"></i>
                </td>
                <td class='text-truncate'
                    style="max-width: 0;"
                    v-bind:title="entities[eid].name">{{entities[eid].name}}</td>
                <td class='text-nowrap pe-3 actions'>
                  <span v-show="editableVisibility">
                    <i class='fa fa-eye text-primary actionable'
                       title='Click to hide this entity'
                       v-show="!overrides[eid]?.hidden" @click="toggleEntityVisibility(eid)"></i>
                    <i class='fa fa-eye-slash text-primary actionable'
                       title='Click to show this entity'
                       v-show="overrides[eid]?.hidden" @click="toggleEntityVisibility(eid)"></i>
                  </span>
                  <i @click="focusEntity(eid)"
                     v-show="!overrides[eid]?.hidden"
                     class='fa fa-crosshairs text-primary actionable ms-1'
                     title="Center graph on this entity"></i>
                </td>
              </tr>
            </tbody>
            <tbody v-else>
              <tr>
                <td colspan="4">No entities found</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div class="footer">
          <button @click="close()" type="button"
                  class="btn btn-outline-secondary"
                  role="close">Close</button>
      </div>
    </div>
  </div>
</template>
