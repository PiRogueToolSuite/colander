<script>
import EntitiesTablePane from "./graph-editor/EntitiesTablePane.vue";
import EntityOverviewPane from "./graph-editor/EntityOverviewPane.vue";
import EntityEditPane from "./graph-editor/EntityEditPane.vue";
import RelationEditPane from "./graph-editor/RelationEditPane.vue";
import SubgraphCreationPane from "./graph-editor/SubgraphCreationPane.vue";

import ColanderDGraph from "./graph-editor/engine";

export default {
  components: {
    EntitiesTablePane, EntityOverviewPane, EntityEditPane, RelationEditPane, SubgraphCreationPane,
  },
  props: {
    dataCsrfToken: String,
    dataSrc: String,
    dataDock: Boolean,
    dataCaseId: String,
    dataSubgraphId: String,
  },
  data() {
    return {
      sidepane: {
        active: false,
        vue: null,
      },
    };
  },
  created() {
    this.$logger(this, 'GraphEditor');
  },
  mounted() {
    this.$graphOptions = {
      containerId: 'a-colander-graph',
      csrfToken: this.dataCsrfToken,
      sendToDocumentation: false,
      datasourceUrl: this.dataSrc,
    };
    if (this.dataCaseId) {
      Object.assign(this.$graphOptions, {
        caseId: this.dataCaseId,
        generateThumbnail: false,
        editableVisibility: false,
      });
    }
    if (this.dataSubgraphId) {
      Object.assign(this.$graphOptions, {
        subgraphId: this.dataSubgraphId,
        generateThumbnail: true,
        editableVisibility: true,
      });
    }
    if (this.lock) {
      Object.assign(this.$graphOptions, {
        lock: true,
      });
    }
    else {
      Object.assign(this.$graphOptions, {
        recenter: true,
        snapshot: true,
        fullscreen: true,
        sidepane: true,
      });
    }
    this.$debug('GraphOptions', this.$graphOptions);
    this.$graph = new ColanderDGraph(this, this.$graphOptions);
  },
  methods: {
    setSidepane(boolOrVue) {
      if (typeof(boolOrVue) === 'boolean') {
        this.sidepane.active = boolOrVue;
      }
      else {
        this.sidepane.vue = boolOrVue;
        this.sidepane.active = true;
      }
    }
  },
}
</script>
<template>
  <div id="a-colander-graph" :class="{'colander-dgraph': true, 'sidepane-active': sidepane.active}">
    <div class='graph-sub-container'/>
    <div class="graph-overlay-menu position-absolute top-0 start-0" style="z-index: 20;"/>
    <div class="graph-loading">
      <div class="spinner-border" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>
    <div class='sidepane'>
      <EntitiesTablePane ref="entityTablePane" :class="{ active: sidepane.vue === $refs.entityTablePane }"/>
      <EntityEditPane ref="entityEditPane" :class="{ active: sidepane.vue === $refs.entityEditPane }"/>
      <RelationEditPane ref="relationEditPane" :class="{ active: sidepane.vue === $refs.relationEditPane }"/>
      <EntityOverviewPane ref="entityOverviewPane" :class="{ active: sidepane.vue === $refs.entityOverviewPane }"/>
      <SubgraphCreationPane ref="subgraphCreationPane" :class="{ active: sidepane.vue === $refs.subgraphCreationPane }"/>
    </div>
  </div>
</template>
