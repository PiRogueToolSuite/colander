<script setup>
</script>
<script>
export default {
  props: {
    dataActionUrl: String,
    dataCaseId: String,
    dataCsrfToken: String,
  },
  data() {
    return {
      currentSearch: '',
      results: [],
    };
  },
  methods: {
      updateResult: async function() {
          const csrfDom = document.querySelector("#overall-search-form input[name=csrfmiddlewaretoken]");
          const caseIdDom = document.querySelector("#overall-search-form input[name=case_id]");
          var queryPost = {
              case_id: caseIdDom?.value,
              query: this.currentSearch,
          };
          try {
              const searchResponse = await fetch('/rest/search', {
                  method: 'POST',
                  headers: {
                      'Accept': 'application/json',
                      'Content-Type': 'application/json',
                      'X-CSRFToken': csrfDom.value,
                  },
                  body: JSON.stringify(queryPost),
              });
              if (!searchResponse.ok) {
                throw new Error('Unexcpeted server error');
              }
              this.results = await searchResponse.json();
          } catch(e) {
              console.error("Unable to search", e);
          }
      },
      startDrag(evt, item) {
          console.log('startDrag', evt, item);
          evt.dataTransfer.dropEffect = "link";
          evt.dataTransfer.setData("text/markdown", `[${item.name}](${item.url})`);
      }
  },
  watch: {
      currentSearch(newValue, oldValue) {
          if (this._debounced_handler) {
              clearTimeout(this._debounced_handler);
              this._debounced_handler = null;
          }
          this._debounced_handler = setTimeout(this.updateResult.bind(this), 300);
      }
  },
  computed: {},
};
</script>
<template>
<div class='vue-container'>
  <form id="overall-search-form" method="POST" :action="dataActionUrl">
    <input type='hidden' name="csrfmiddlewaretoken" :value="dataCsrfToken" />
    <input type='hidden' name='case_id' :value='dataCaseId'/>
    <input id="overall-search" v-model="currentSearch" class="form-control font-monospace fst-italic form-control-dark w-100" name="q" type="text" placeholder="Search" aria-label="Search" autocomplete="off" />
    <i id="overall-search-icon" class="nf nf-md-magnify" aria-hidden="true"></i>
    <div id="overall-search-result" v-if="results.length > 0">
      <div class="list-group">
        <a v-for="r in results" v-bind:href="r.url" class="list-group-item list-group-item-action" draggable="true" @dragstart="startDrag($event, r)">
          <div class="d-flex w-100 justify-content-between">
            <h5 class="mb-1">
              <i class="fa fa-circle" v-bind:style="{color:r.color}" data-bs-toggle="tooltip" data-bs-placement="top" v-bind:title="r.model_name"></i>
              <i v-if="r.tlp == 'WHITE' || r.tlp == 'CLEAR'" class="ms-1 fa fa-circle text-muted" data-bs-toggle="tooltip" data-bs-placement="top" title="TLP:CLEAR"></i>
              <i v-else-if="r.tlp == 'GREEN'" class="ms-1 fa fa-circle text-success" data-bs-toggle="tooltip" data-bs-placement="top" title="TLP:GREEN"></i>
              <i v-else-if="r.tlp == 'AMBER'" class="ms-1 fa fa-circle text-warning" data-bs-toggle="tooltip" data-bs-placement="top" title="TLP:AMBER"></i>
              <i v-else-if="r.tlp == 'RED'" class="ms-1 fa fa-circle text-danger" data-bs-toggle="tooltip" data-bs-placement="top" title="TLP:RED"></i>
              <i v-else class="ms-1 fa fa-circle text-muted" data-bs-toggle="tooltip" data-bs-placement="top" title="No TLP"></i>
              <i v-if="r.pap == 'WHITE' || r.pap == 'CLEAR'" class="ms-1 fa fa-circle text-muted" data-bs-toggle="tooltip" data-bs-placement="top" title="PAP:CLEAR"></i>
              <i v-else-if="r.pap == 'GREEN'" class="ms-1 fa fa-circle text-success" data-bs-toggle="tooltip" data-bs-placement="top" title="PAP:GREEN"></i>
              <i v-else-if="r.pap == 'AMBER'" class="ms-1 fa fa-circle text-warning" data-bs-toggle="tooltip" data-bs-placement="top" title="PAP:AMBER"></i>
              <i v-else-if="r.pap == 'RED'" class="ms-1 fa fa-circle text-danger" data-bs-toggle="tooltip" data-bs-placement="top" title="PAP:RED"></i>
              <i v-else class="ms-1 fa fa-circle text-muted" data-bs-toggle="tooltip" data-bs-placement="top" title="No PAP"></i>
              <i v-if="r.is_malicious" class="ms-1 fa fa-circle text-danger" data-bs-toggle="tooltip" data-bs-placement="top" title="Malicious"></i>
              <i v-else class="ms-1 fa fa-circle text-muted" data-bs-toggle="tooltip" data-bs-placement="top" title="No threat"></i>
              <i v-if="r.type_icon" v-bind:class="['ms-1', 'nf', r.type_icon, 'text-muted']" data-bs-toggle="tooltip" data-bs-placement="top" v-bind:title="r.type"></i>
              {{r.name}}
            </h5>
            <small class="text-muted">{{r.model_name}} - {{r.type}}</small>
          </div>
          <!--
          <p class="mb-1">{{r.tlp}} {{r.pap}} {{r.type}} {{r.model_name}}</p>
          -->
          <small class="text-muted">Case : {{r.case}}</small>
        </a>
      </div>
    </div>
  </form>
</div>
</template>
<style scoped>
</style>
