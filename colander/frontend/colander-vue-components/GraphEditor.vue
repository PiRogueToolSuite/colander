<script setup>
import EntitiesTablePane from "./graph-editor/EntitiesTablePane.vue";
import EntityOverviewPane from "./graph-editor/EntityOverviewPane.vue";
import EntityEditPane from "./graph-editor/EntityEditPane.vue";
import RelationEditPane from "./graph-editor/RelationEditPane.vue";
import SubgraphCreationPane from "./graph-editor/SubgraphCreationPane.vue";

import ColanderDGraph from "./graph-editor/engine";
</script>
<script>
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
  created() {

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
    console.log('GraphOptions', this.$graphOptions);
    this.$graph = new ColanderDGraph(this.$graphOptions);
  },
}
</script>
<template>
  <div class="colander-dgraph">
    <div class='graph-sub-container'/>
    <div class="graph-overlay-menu position-absolute top-0 start-0" style="z-index: 20;"/>
    <div class="graph-loading">
      <div class="spinner-border" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>
    <div class='sidepane'>
      <div class="vue-component">
        <EntitiesTablePane/>
      </div>
      <div class="vue-component">
        <EntityEditPane/>
      </div>
      <div class="vue-component">
        <RelationEditPane/>
      </div>
      <div class="vue-component">
        <EntityOverviewPane/>
      </div>
      <div class="vue-component">
        <SubgraphCreationPane/>
      </div>
    </div>
  </div>
</template>
<style scoped>
</style>
