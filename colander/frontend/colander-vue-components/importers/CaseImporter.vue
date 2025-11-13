<script>
import TlpPap from "../utils/TlpPap.vue";
import DateInfo from "../utils/DateInfo.vue";
import {Button, Card, Column, DataTable, FileUpload, Panel, ProgressBar, Tag} from "primevue";
import {BlobReader, TextWriter, ZipReader} from "@zip.js/zip.js";
import Color from 'color';

export default {
  props: {
    dataCsrfToken: String,
  },
  data() {
    return {
      currentCaseFile: null,
      state: {
        title: 'Please choose a file',
        error: null,
        progress: 0,
        determinate: true,
      },
      caseInfo: null,
      manifestInfo: null,
      caseEntries: [],
      _styles: {},
    };
  },
  components: {
    Button,
    Card,
    Column,
    DateInfo,
    DataTable,
    FileUpload,
    Panel,
    ProgressBar,
    Tag,
    TlpPap,
  },
  created() {
    this.$logger(this, 'CaseImporter');
    this.$cache.retrieve('all_styles').then((styles) => {
      this.$debug('got styles', styles);
      this._styles = styles;
    });
  },
  methods: {
    _setState(progress, title, error) {
      if (title !== undefined) {
        this.state.title = title;
      }

      this.state.error = error || null;

      if (progress !== undefined) {
        if (progress < 0) {
          this.state.determinate = false;
        }
        else {
          this.state.determinate = true;
          this.state.progress = Math.floor(progress * 100);
        }
      }
    },
    fileSelected(evt) {
      this._setState(-1, 'Parsing metadata ...');

      for(let file of evt.files) {
        this.parseFile(file);
        return; // parse only one file
      }
    },
    async parseFile(file) {
      this.currentCaseFile = file;
      const zipFileReader = new BlobReader(file);
      const zipReader = new ZipReader(zipFileReader);
      const zipEntries = await zipReader.getEntries();
      const zipEntriesCount = zipEntries.length;

      let entryProcessed = 0;
      for(let zipEntry of zipEntries) {
        if (zipEntry.filename.endsWith('data.json')) {
          this.$debug(`Processing: ${zipEntry.filename}`);
          const jsonWriter = new TextWriter();
          const jsonContent = await zipEntry.getData(jsonWriter);
          const data = JSON.parse(jsonContent);
          let typeStr = 'Case';
          const filenameParts = zipEntry.filename.split('/');
          if (filenameParts.length > 1) {
            typeStr = filenameParts[0];
          }
          let newEntry = {
            filename: zipEntry.filename,
            name: data.name,
            super_type: typeStr,
            type: data.type?.name,
            thumbnail: Boolean(data.thumbnail),
            file: data.size_in_bytes > 0,
            warning: false,
            data: data,
          };
          if (zipEntry.filename === 'data.json') {
            this.caseInfo = newEntry;
            this.$debug('caseInfo', newEntry);
          }
          else {
            this.caseEntries.push(newEntry);
          }
        }
        else if (zipEntry.filename === 'manifest.json') {
          this.$debug(`Processing: ${zipEntry.filename}`);
          const jsonWriter = new TextWriter();
          const jsonContent = await zipEntry.getData(jsonWriter);
          const data = JSON.parse(jsonContent);
          this.manifestInfo = data;
        }
        entryProcessed += 1;
        this._setState(entryProcessed/zipEntriesCount);
      }
      await zipReader.close();
      if (this.caseInfo === null) {
        this._setState(1, "Metadata not found.", "No case information found.");
      }
      else if (this.manifestInfo === null) {
        this._setState(1, "Metadata not found.", "No manifest information found.");
      }
      else {
        this._setState(1, "Metadata parsed. Please review then hit 'Import case' button.");
      }
    },
    reset(cb) {
      this.currentCaseFile = null;
      this.state.determinate = true;
      this.state.progress = 0;
      this.state.title = 'Please choose a file';
      this.state.error = null;
      this.caseInfo = null;
      this.manifestInfo = null;
      this.caseEntries = [];
      cb?.();
    },
    importCurrentCase() {

    },
    iconClass(data) {
      if (data.super_type === 'Case') {
        return 'fa fa-folder';
      }
      if (data.super_type === 'SubGraph') {
        return 'nf nf-md-hubspot';
      }
      if (data.super_type in this._styles) {
        let iconCls = this._styles[data.super_type]?.['icon-font-classname'];
        let iconSet = iconCls.split('-');
        return `${iconSet[0]} ${iconCls}`;
      }
      return '';
    },
    typeColor(data) {
      if (data.super_type === 'Case') {
        return '#A991D4';
      }
      if (data.super_type === 'SubGraph') {
        return 'rgba(42, 123, 155, 1)';
      }
      if (data.super_type in this._styles) {
        return this._styles[data.super_type]?.color;
      }
      return null;
    },
    rs_obj(data) {
      let colorStr = this.typeColor(data);
      if (!colorStr) return {};
      let baseStyle = {
        '--super-type-bg-color': this.typeColor(data) || 'red',
        //'top': '39px',
      };
      let colorObj = Color(colorStr);
      if (colorObj.luminosity() < 0.6) {
        //baseStyle['--super-type-fg-color'] = 'white';
      }
      return baseStyle;
    },
  },
  computed: {
    stateMode() {
      return this.state.determinate ? 'determinate' : 'indeterminate';
    },
    invalidImport() {
      return this.caseInfo === null || this.manifestInfo === null || this.state.error !== null;
    },
  },
};
</script>
<template>
  <div class="case-importer">
    <FileUpload ref="fileChooser"
                accept="application/zip"
                @select="fileSelected">
      <template #header="{chooseCallback, clearCallback, files}">
        <div v-if="files.length">
          <Button label="Cancel"
                  icon="pi pi-undo" severity="danger"
                  @click="reset(clearCallback)"/>
          <Button label="Import case"
                  icon="pi pi-file-arrow-up" severity="primary"
                  class="ms-2"
                  :disabled="invalidImport"
                  @click="importCurrentCase()"/>
        </div>
        <div v-else>
          <Button label="Choose"
                  icon="fa fa-folder-open" severity="primary"
                  @click="chooseCallback"/>
        </div>
      </template>
      <template #content>
        <div class="">
          <span>{{ state.title }}</span>
          <span v-if="state.error" class="text-danger ms-2">
            <i class="pi pi-exclamation-triangle"></i> {{ state.error }}
          </span>
        </div>
        <ProgressBar :value="state.progress" :mode="stateMode"></ProgressBar>
      </template>
    </FileUpload>
    <div class="row mt-2">
      <div class="col-12">
        <Panel v-show="!invalidImport">
          <template #header>
            <h4>{{ caseInfo?.name }}</h4>
          </template>
          <div class="row">
            <div class="col-lg-6">
              <table class="table table-sm">
                <tbody>
                  <tr>
                    <td>Created at</td>
                    <td>
                      <DateInfo v-if="caseInfo?.data.created_at" :date="caseInfo?.data.created_at"/>
                    </td>
                  </tr>
                  <tr>
                    <td>Updated at</td>
                    <td>
                      <DateInfo v-if="caseInfo?.data.updated_at" :date="caseInfo?.data.updated_at"/>
                    </td>
                  </tr>
                  <tr>
                    <td>TLP/PAP</td>
                    <td>
                      <TlpPap :tlp="caseInfo?.data.tlp" :pap="caseInfo?.data.pap" />
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="col-lg-6">
              <h5>Description</h5>
              <pre>{{caseInfo?.data.description}}</pre>
            </div>
          </div>
          <h4>Case content</h4>
          <DataTable :value="caseEntries"
                     rowGroupMode="subheader" groupRowsBy="super_type"
                     :rowStyle="rs_obj"
                     :pt="{
                       rowGroupHeader: (options) => ({
                         style: rs_obj(options.props.rowData),
                       }),
                     }">
            <Column field="name" header="Name">
              <template #body="slotProps">
                <div class="type-colored">
                  <i :class="iconClass(slotProps.data)"></i>
                  <span class="ms-1">{{slotProps.data.name}}</span>
                </div>
              </template>
            </Column>
            <Column field="super_type" header="Super Type"/>
            <Column field="type" header="Type"/>
            <Column field="thumbnail" header="Has thumbnail">
              <template #body="slotProps">
                <Tag v-if="slotProps.data.thumbnail" icon="pi pi-check" severity="secondary"></Tag>
              </template>
            </Column>
            <Column field="file" header="Has file">
              <template #body="slotProps">
                <Tag v-if="slotProps.data.file" icon="pi pi-check" severity="secondary"></Tag>
              </template>
            </Column>
            <Column field="warning" header="Status">
              <template #body="slotProps">
                <Tag severity="success">Ready</Tag>
              </template>
            </Column>
            <template #groupheader="slotProps">
              <div class="gap-2 type-colored white-outline">
                <i :class="iconClass(slotProps.data)"></i>
                <span class="ms-1 fw-bold">{{ slotProps.data.super_type }}</span>
              </div>
            </template>
          </DataTable>
        </Panel>
      </div>
    </div>
  </div>
</template>
<style scoped>
.p-progressbar {
  --p-fileupload-progressbar-height: 1.25em;
}
:global(tr:has(.type-colored)) {
  --falloff-distance: 5px;
  --super-type-bg-color: rgba(42, 123, 155, 1);
  --super-type-fg-color: var(--p-datatable-row-color);
  background: linear-gradient(
    90deg,
    var(--super-type-bg-color) 0%,
    var(--super-type-bg-color) 4px,
    white var(--falloff-distance)
  ) !important;
}
:global(tr.p-datatable-row-group-header:has(.type-colored)) {
  color: var(--super-type-fg-color) !important;
  --falloff-distance: 50%;
}
:global(.white-outline) {
  --offset: 2px;
  --distance: 1px;
  text-shadow:
      white 0 var(--offset) var(--distance),
      white 0 calc(-1*var(--offset)) var(--distance),
      white var(--offset) 0 var(--distance),
      white calc(-1*var(--offset)) 0 var(--distance),
      white var(--offset) var(--offset) var(--distance),
      white calc(-1*var(--offset)) var(--offset) var(--distance),
      white calc(-1*var(--offset)) calc(-1*var(--offset)) var(--distance),
      white var(--offset) calc(-1*var(--offset)) var(--distance);
}
</style>
