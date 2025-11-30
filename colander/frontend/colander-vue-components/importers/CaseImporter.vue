<script>
import LargeFileUpload from "../legacy/file_upload";
import TlpPap from "../utils/TlpPap.vue";
import DateInfo from "../utils/DateInfo.vue";
import {
  Button,
  Card,
  Column,
  DataTable,
  FileUpload,
  MeterGroup,
  Panel,
  ProgressBar,
  ProgressSpinner,
  Tag
} from "primevue";
import {BlobReader, BlobWriter, TextWriter, ZipReader, getMimeType} from "@zip.js/zip.js";
import Color from 'color';
import Checkbox from "primevue/checkbox";

const FK_TO_REMAP = [
          'operated_by',
          'extracted_from',
          'associated_threat',
          'observed_on', 'detected_by', 'attributed_to', 'target',
          'pcap', 'socket_trace', 'target_device', 'target_artifact', 'sslkeylog', 'screencast', 'aes_trace',
          'obj_from_id', 'obj_to_id'];
const LIST_TO_REMAP = ['extra_files', 'involved_observables', 'targeted_observables'];
const DICT_TO_REMAP = ['overrides'];


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
        progress: {
          parsing: 0,
          import: 0,
          remapping: 0,
        },
      },
      caseInfo: null,
      manifestInfo: null,
      caseEntries: [],
      idRemapping: {},
      _styles: {},
    };
  },
  components: {
    Button,
    Card,
    Checkbox,
    Column,
    DateInfo,
    DataTable,
    FileUpload,
    MeterGroup,
    Panel,
    ProgressBar,
    ProgressSpinner,
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
    _setState(phase, progress, title, error) {
      if (title !== undefined) {
        this.state.title = title;
      }

      this.state.error = error || null;

      if (progress !== undefined) {
        if (progress < 0) {
          // Do not set
        }
        else {
          this.state.progress[phase] = Math.floor(progress * 100);
        }
      }
    },
    async fileSelected(evt) {
      this._setState('parsing', -1, 'Parsing metadata ...');

      for(let file of evt.files) {
        await this.parseFile(file);
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

      // First-pass: metadata / json parsing
      for(let zipEntry of zipEntries) {
        let filenameParts = zipEntry.filename.split('/');
        let idFromPath = filenameParts.length === 3 ? filenameParts[1] : false;

        if (zipEntry.filename.endsWith('data.json')) {
          const jsonWriter = new TextWriter();
          const jsonContent = await zipEntry.getData(jsonWriter);
          const data = JSON.parse(jsonContent);
          let typeStr = 'Case';
          if (filenameParts.length > 1) {
            typeStr = filenameParts[0];
          }
          let newEntry = {
            filename: zipEntry.filename,
            name: data.name,
            super_type: typeStr,
            type: data.type?.name,
            thumbnail: false,
            file: false,
            status: 'Ready',
            data: data,
          };

          if (idFromPath) {
            if (idFromPath !== newEntry.data.id) {
              newEntry.status = "ID Mismatch";
            }
          }

          this.idRemapping[newEntry.data.id] = this.idRemapping[newEntry.data.id] || {};
          Object.assign(this.idRemapping[newEntry.data.id], newEntry);

          if (zipEntry.filename === 'data.json') {
            this.caseInfo = this.idRemapping[newEntry.data.id];
          }
          else {
            this.caseEntries.push(this.idRemapping[newEntry.data.id]);
          }
          this.$debug('new entry', newEntry);
        }
        else if (zipEntry.filename.endsWith('thumbnail.png')) {
          if (!idFromPath) break;
          this.idRemapping[idFromPath] = this.idRemapping[idFromPath] || {};
          let blob = await zipEntry.getData(new BlobWriter(getMimeType(zipEntry.filename)));
          Object.assign(this.idRemapping[idFromPath], { 'thumbnail': new File([blob], zipEntry.filename) });
        }
        else if (zipEntry.filename === 'manifest.json') {
          const jsonWriter = new TextWriter();
          const jsonContent = await zipEntry.getData(jsonWriter);
          this.manifestInfo = JSON.parse(jsonContent);
        }
        else {
          if (!idFromPath) break;
          this.idRemapping[idFromPath] = this.idRemapping[idFromPath] || {};
          let fileName = this.idRemapping[idFromPath].data.name;
          let blob = await zipEntry.getData(new BlobWriter(getMimeType(fileName)));
          Object.assign(this.idRemapping[idFromPath], { 'file': new File([blob], fileName) });
        }

        entryProcessed += 1;
        this._setState('parsing', entryProcessed/zipEntriesCount);
      }

      await zipReader.close();

      if (this.caseInfo === null) {
        this._setState('parsing', -1, "Metadata not found.", "No case information found.");
      }
      else if (this.manifestInfo === null) {
        this._setState('parsing', -1, "Metadata not found.", "No manifest information found.");
      }
      else {
        this._setState('parsing', 1, "Parsing done. Ready to import.");
      }
    },
    reset(cb) {
      this.currentCaseFile = null;
      this.state.progress.parsing = 0;
      this.state.progress.import = 0;
      this.state.progress.remapping = 0;
      this.state.title = 'Please choose a file';
      this.state.error = null;
      this.caseInfo = null;
      this.manifestInfo = null;
      this.caseEntries = [];
      cb?.();
    },
    async _createEntry(entry, phase, withRemap) {
      if (entry.super_type !== 'Case') {
        entry.data.case = this.caseInfo.data.id;
      }

      let json_payload = this.entry_to_json(entry);
      if (withRemap) {
        let remapped_relation = this.entry_remap_json(entry);
        json_payload = Object.assign(json_payload, remapped_relation);
      }

      let res = await fetch(`/archives/import/${entry.super_type}/create`, {
        method: 'POST',
        headers: {
          "X-CSRFToken": this.dataCsrfToken,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(json_payload),
      });

      if (!res.ok) {
        this._setState(phase, -1, "Creation failed", res.statusText);
        throw new Error(`${phase} failed: ${res.statusText}`);
      }

      let entity = await res.json();
      entry.data.id = entity.id;
      this.$debug(`${entry.super_type} created`, entity);

      // Thumbnail
      if (entry.thumbnail) {
        let formData = new FormData();
        formData.append('thumbnail', entry.thumbnail);
        res = await fetch(`/archives/import/${entry.super_type}/attach/${entry.data.id}`, {
          method: 'POST',
          headers: {
            "X-CSRFToken": this.dataCsrfToken,
          },
          body: formData,
        });

        if (!res.ok) {
          this._setState(phase, -1, "Thumbnail failed", res.statusText);
          throw new Error(`${phase} thumbnail failed: ${res.statusText}`);
        }
      }

      // File
      if (entry.file) {
        let upload_request;
        try {
          let uploader = new LargeFileUpload({
            csrf_token: this.dataCsrfToken,
          });
          upload_request = await uploader.upload_async(entry.file);
          upload_request = await uploader.update_upload_request({
            target_entity_id: entry.data.id,
          });
        } catch(uploader_error) {
          this._setState(phase, -1, "Creation file failed", `${uploader_error}`);
          throw new Error(`${phase} file failed: ${uploader_error}`);
        }

        if (!upload_request) {
          this._setState(phase, -1, "Creation file failed", `No upload request created`);
          throw new Error(`${phase} file failed: No upload request created`);
        }

        res = await fetch(`/archives/import/${entry.super_type}/remap/${entry.data.id}`, {
          method: 'POST',
          headers: {
            "X-CSRFToken": this.dataCsrfToken,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({'upload_request_ref': upload_request.id}),
        });

        if (!res.ok) {
          this._setState(phase, -1, "Creation file failed", res.statusText);
          throw new Error(`${phase} file failed: ${res.statusText}`);
        }
      }

      entry.status = 'Prepared';
    },
    async _remapEntry(entry) {
      let idToRemap = entry.data.id;
      let json_payload = this.entry_remap_json(entry);
      let res = await fetch(`/archives/import/${entry.super_type}/remap/${idToRemap}`, {
        method: 'POST',
        headers: {
          "X-CSRFToken": this.dataCsrfToken,
          "Content-Type": "application/json",
        },
        body: JSON.stringify( json_payload ),
      });

      if (!res.ok) {
        this._setState('remapping', -1, "Remapping failed", res.statusText);
        throw new Error(`remapping: failed: ${res.statusText}`);
      }
      entry.status = 'Imported';
    },
    async importAll() {
      this._setState('import', 0, "Archive import ...");
      let totalImports = 1 + this.caseEntries.length;
      let proceedImport = 0;

      // TODO: Clean
      this.caseInfo.data.name += " (Imported)";

      await this._createEntry(this.caseInfo, 'import', false);

      proceedImport++;
      this._setState('import', proceedImport/totalImports);

      for(let cE of this.caseEntries) {
        if (cE.super_type === "EntityRelation") continue;
        if (cE.super_type === "PiRogueExperiment") continue;
        await this._createEntry(cE, 'import', false);
        proceedImport++;
        this._setState('import', proceedImport/totalImports);
      }

      for(let cE of this.caseEntries) {
        if (cE.super_type !== "EntityRelation" && cE.super_type !== "PiRogueExperiment") continue;
        await this._createEntry(cE, 'import', true);
        proceedImport++;
        this._setState('import', proceedImport/totalImports);
      }

      this._setState('import', 1, "Success");

      await this.remap();
    },
    async remap() {
      this._setState('remapping', 0, "Remapping ...");
      let totalRemaps = 1 + this.caseEntries.length;
      let proceedRemap = 0;

      await this._remapEntry(this.caseInfo);

      proceedRemap++;
      this._setState('remapping', proceedRemap/totalRemaps);

      for(let cE of this.caseEntries) {
        await this._remapEntry(cE);

        proceedRemap++;
        this._setState('remapping', proceedRemap/totalRemaps);
      }
      this._setState('remapping', 1, 'Import successful.');
    },
    entry_to_json(entry) {
      let data = entry.data;
      let formData = {};
      for(let e in data) {
        let v = data[e];
        if (v === null) continue;
        if (FK_TO_REMAP.includes(e)) continue;
        if (LIST_TO_REMAP.includes(e)) continue;
        if (DICT_TO_REMAP.includes(e)) continue;
        formData[e] = v;
      }

      return formData;
    },
    entry_remap_json(entry) {
      let data = entry.data;
      let json = {};
      for(let e in data) {
        if (data[e] === null) continue;

        // Remap FK with uuid as value
        if (FK_TO_REMAP.includes(e)) {
          json[e] = this.idRemapping[data[e]].data.id;
          continue;
        }

        // Remap dict with uuid as key
        if (DICT_TO_REMAP.includes(e)) {
          json[e] = {};
          for(let oid in data[e]) {
            if (!this.idRemapping[oid] && e === 'overrides') continue; // Skipable : overrides are weak references
            let newId = this.idRemapping[oid].data.id;
            json[e][newId] = data[e][oid];
          }
          continue;
        }

        // Remap array with uuid as values
        if (LIST_TO_REMAP.includes(e)) {
          json[e] = [];
          for(let oid of data[e]) {
            let newId = this.idRemapping[oid].data.id;
            json[e].push(newId);
          }
        }
      }
      return json;
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
        '--super-type-bg-color': colorStr || 'red',
        //'top': '39px',
      };
      let colorObj = Color(colorStr);
      if (colorObj.luminosity() < 0.6) {
        //baseStyle['--super-type-fg-color'] = 'white';
      }
      return baseStyle;
    },
    entitySeverity(status) {
      if (status === 'Pending') return 'secondary';
      if (status === 'Prepared') return 'secondary';
      if (status === 'Imported') return 'success';
      return status;
    },
  },
  computed: {
    invalidParsing() {
      return this.caseInfo === null || this.manifestInfo === null;
    },
    hasError() {
      return this.state.error !== null;
    },
    invalidImport() {
      return this.invalidParsing || this.hasError;
    },
    totalProgress() {
      return this.state.progress.import + this.state.progress.remapping;
    },
    uploading() {
      return this.totalProgress > 0 && !this.hasError && !this.importationComplete;
    },
    importationComplete() {
      return this.totalProgress === 200 && !this.hasError;
    },
    global_progress() {
      return [
        {
          label: 'Parsing',
          color: 'var(--bs-warning)',
          value: this.state.progress.parsing,
        },
        {
          label: 'Import',
          color: 'var(--bs-secondary)',
          value: this.state.progress.import,
        },
        {
          label: 'Remapping',
          color: 'var(--bs-primary)',
          value: this.state.progress.remapping,
        },
      ];
    }
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
          <div v-if="uploading">
            <ProgressSpinner
                style="width: 34px; height: 34px" strokeWidth="4" fill="transparent"
                animationDuration="1s" aria-label="Importation ..." />
          </div>
          <div v-else-if="importationComplete">
            <Button label="Import another Case"
                    icon="pi pi-undo" severity="secondary"
                    @click="reset(clearCallback)"/>
          </div>
          <div v-else>
            <Button label="Cancel"
                    icon="pi pi-undo" severity="danger"
                    @click="reset(clearCallback)"/>
            <Button label="Import case"
                    icon="pi pi-file-arrow-up" severity="primary"
                    class="ms-2"
                    :disabled="invalidImport"
                    @click="importAll()"/>
          </div>
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
        <MeterGroup :value="global_progress" :max="300" />
      </template>
    </FileUpload>
    <div class="row mt-2">
      <div class="col-12">
        <Panel v-show="!invalidParsing">
          <template #header>
            <h4>{{ caseInfo?.name }}
              <Tag :severity="entitySeverity(caseInfo?.status)">{{caseInfo?.status || 'Ready'}}</Tag>
            </h4>
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
                <Tag v-if="slotProps.data.thumbnail !== false" icon="pi pi-check" severity="secondary"></Tag>
              </template>
            </Column>
            <Column field="file" header="Has file">
              <template #body="slotProps">
                <Tag v-if="slotProps.data.file !== false" icon="pi pi-check" severity="secondary"></Tag>
              </template>
            </Column>
            <Column field="status" header="Status">
              <template #body="slotProps">
                <Tag :severity="entitySeverity(slotProps.data.status)">{{slotProps.data.status}}</Tag>
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
