<template>
  <div class="csv-viewer">
    <Toast/>
    <div class="row">
      <div class="col-12">
        <h4>Import CSV</h4>
        <Toolbar>
          <template #start>
            <FileUpload
              mode="basic"
              name="csv-file"
              :auto="true"
              accept=".csv"
              :maxFileSize="1000000"
              chooseLabel="Select CSV File"
              @select="onFileSelect"
            />
            <Select
              v-model="this.selectedSuperType"
              :default-value="this.selectedSuperType"
              :options="this.availableSuperTypes"
              :loading
              filter
              optionLabel="name"
              placeholder="Select entity type"
              class="mx-2" />
          </template>

          <template #center>
            <InputGroup class="mx-2">
              <InputGroupAddon>Delimiter</InputGroupAddon>
              <InputText v-model="this.delimiter"/>
            </InputGroup>
            <InputGroup class="mx-2">
              <InputGroupAddon>Quote char</InputGroupAddon>
              <InputText v-model="this.quoteChar"/>
            </InputGroup>
            <InputGroup class="mx-2">
              <InputGroupAddon>Escape char</InputGroupAddon>
              <InputText v-model="this.escapeChar"/>
            </InputGroup>
          </template>

          <template #end>
            <Button
              label="Reload"
              severity="secondary"
              :disabled="!this.inputFile"
              icon="pi pi-refresh"
              @click="this.parseFile"/>
            <Button
              label="Dump"
              :disabled="!this.inputFile"
              @click="this.dump"/>
          </template>
        </Toolbar>
      </div>
    </div>

    <div class="row mt-2">
      <div class="col-12">
        <Panel header="Mapping">
           <div v-if="error" class="p-error p-mt-2">
            {{ this.error }}
          </div>
          <div v-if="this.tableData.length === 0 && !this.loading" class="p-text-center p-mt-4">
            <p>No data loaded. Please select a CSV file to view.</p>
          </div>
          <DataTable
          :value="this.tableData"
          :loading
          scrollable
          removableSort
          resizableColumns
          columnResizeMode="fit"
          size="small"
          v-if="this.tableData.length > 0"
        >
          <template #header>
            <div class="mt-1">
              Type: <Select
                v-model="this.defaultType"
                :options="this.availableTypes"
                :loading
                filter
                optionLabel="name"
                placeholder="Default type"
                @change="this.applyDefaultType"
                class="me-2" />
              Show/hide columns: <MultiSelect :modelValue="this.selectedColumns" :options="this.columns" optionLabel="header" :loading
                           @update:modelValue="this.onToggleColumn" display="chip" placeholder="Select Columns" />
            </div>
            <div class="mt-3 text-muted">
              <i class="pi pi-info-circle text-info"></i> You are about to create {{ this.tableData.length }} entities
              of type {{ this.selectedSuperType.name }}.
              Map the entity properties to the columns of your CSV. Available properties:
              <ul>
                <li v-for="field of this.availableFields">
                  <i class="pi pi-check" style="color: var(--p-lime-500)" v-if="field.mappingSuccess"></i>
                  <i class="pi pi-times" style="color: var(--p-red-500)" v-if="field.mappingError"></i>
                  {{ field.label }}
                  (<span class="font-monospace fst-italic">{{ field.name }}</span>):
                  <span v-if="field.required" class="fw-bold">required, </span>
                  <span v-else class="fw-bold">optional, </span>
                  <span v-if="!field.multiple"> can be used only once</span>
                  <span v-else> can be used multiple times</span>
                  <span v-if="field.name==='ignore_field'"> to flag a column as ignored</span>
                </li>
              </ul>
            </div>
          </template>
          <Column header="" frozen>
            <template #body="slotProps">
              <Select
                v-model="slotProps.data.targetType"
                :default-value="this.defaultType"
                :options="this.availableTypes"
                filter
                size="small"
                optionLabel="name"
                placeholder="Select a type"
                class="" />
            </template>
          </Column>
          <Column
            v-for="(col, index) of this.selectedColumns"
            sortable
            :field="col.field"
            :key="col.field + '_' + index"
          >
            <template #header>
              <IftaLabel class="w-100">
                <Select
                  v-model="col.targetField"
                  :options="this.availableFields"
                  filter
                  :input-id="col.field"
                  size="small"
                  optionLabel="label"
                  placeholder="Select field mapping"
                  @valueChange="this.sanityCheck()"/>
                <label :for="col.field" class="font-monospace">{{ col.header }}</label>
              </IftaLabel>
            </template>
          </Column>
        </DataTable>
        </Panel>
        </div>
    </div>
  </div>
</template>
<script>
import Button from "primevue/button";
import Checkbox from "primevue/checkbox";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import FileUpload from "primevue/fileupload";
import IftaLabel from "primevue/iftalabel";
import InputGroup from "primevue/inputgroup";
import InputGroupAddon from "primevue/inputgroupaddon";
import InputText from "primevue/inputtext";
import MultiSelect from "primevue/multiselect";
import Panel from "primevue/panel";
import Papa from "papaparse";
import Select from "primevue/select";
import Tag from "primevue/tag";
import Toast from "primevue/toast";
import Toolbar from "primevue/toolbar";

export default {
  props: {},
  components: {
    Button,
    Checkbox,
    Column,
    DataTable,
    FileUpload,
    IftaLabel,
    InputGroup,
    InputGroupAddon,
    InputText,
    MultiSelect,
    Panel,
    Select,
    Tag,
    Toast,
    Toolbar,
  },
  created() {
    this.$logger(this, 'Csv');
    this.$cache.retrieve('creatable_entities').then((modelsData) => {
      this.models = modelsData;
      this.selectedSuperType = this.getSuperTypeByName('OBSERVABLE');
      this.loading = false;
    });
  },
  mounted() {
    this.$debug('mounted');
    this.loading = true;
  },
  data() {
    return {
      loading: false,
      inputFile: null,
      error: null,
      tableData: [],
      models: [],
      defaultType: null,
      selectedSuperType: null,
      selectedColumns: null,
      columns: [],
      headers: [],
      delimiter: "",
      quoteChar: '"',
      escapeChar: '"',
    };
  },
  methods: {
    dump() {
      console.dir(this.columns);
      console.dir(this.tableData);
    },
    sanityCheck() {
      let valid = true
      this.availableFields.forEach((f) => {
        f.mappingError = false;
        f.mappingSuccess = false;
        f.mappingCount = 0;
        this.columns.forEach((column) => {
          if (column.targetField && column.targetField.name === f.name) {
            f.mappingCount += 1;
            f.mappingSuccess = true;
            if (f.mappingCount > 1 && !column.targetField.multiple) {
              f.mappingSuccess = false;
              f.mappingError = true;
              valid = false;
            }
          }
        });
        if (f.required && f.mappingCount===0) {
          f.mappingSuccess = false;
          f.mappingError = true;
          valid = false
        }
      });
      return valid;
    },
    fieldDisabled(opt) {
      console.log("-----------")
      console.dir(opt)
      this.columns.forEach((column) => {
          if (column.targetField && !column.targetField.multiple && column.targetField.name === opt.name) {
            return true
          }
        });
      return false;
    },
    applyDefaultType() {
      if (this.defaultType) {
        this.tableData.forEach((el) => {
          el.targetType = this.defaultType;
        })
      }
    },
    getSuperTypeByName(name) {
      if (this.models) {
        return this.models.super_types.find(({short_name}) => short_name === name.toUpperCase());
      }
      return null;
    },
    snakeCase(string) {
      return string.replace(/\W+/g, " ")
        .split(/ |\B(?=[A-Z])/)
        .map(word => word.toLowerCase())
        .join('_');
    },
    handleParseError(errors, file) {
      const errorMessages = errors.map(e => e.message).join('; ');
      this.error = `Error parsing CSV: ${errorMessages}`;

      this.$toast.add({
        severity: 'error',
        summary: 'Error',
        detail: `Failed to load ${file.name}: ${errorMessages}`,
        life: 5000
      });

      this.loading = false;
    },
    parseFile() {
      this.loading = true;
      this.error = null;
      this.tableData = [];
      this.columns = [];
      this.headers = [];

      Papa.parse(this.inputFile, {
        header: true,
        transformHeader: this.snakeCase,
        delimiter: this.delimiter,
        quoteChar: this.quoteChar,
        escapeChar: this.escapeChar,
        skipEmptyLines: true,
        complete: (results) => {
          if (results.errors.length > 0) {
            this.handleParseError(results.errors, this.inputFile);
            return;
          }
          if (results.data.length === 0) {
            this.error = 'CSV file is empty or could not be parsed';
            this.$toast.add({
              severity: 'warn',
              summary: 'Empty File',
              detail: this.error,
              life: 5000
            });
            return;
          }
          this.processParsedData(results, this.inputFile);
        },
        error: (error) => {
          this.handleParseError([error], file);
        }
      });
    },
    onFileSelect(event) {
      this.inputFile = event.files[0];
      if (!this.inputFile) return;
      this.parseFile();
    },
    onToggleColumn(val) {
      console.dir(val)
      this.selectedColumns = this.columns.filter(col => val.includes(col));
    },
    processParsedData(results, file) {
      this.tableData = results.data.map(row => ({
        ...row,
        targetType: null,
      }));
      this.columns = results.meta.fields.map(field => ({
        field: field,
        header: field,
        targetField: null
      }));
      this.$toast.add({
        severity: 'success',
        summary: 'File Loaded',
        detail: `${file.name} has been successfully loaded with ${this.tableData.length} rows`,
        life: 3000
      });
      this.selectedColumns = this.columns;
      this.loading = false;
    },
  },
  computed: {
    availableFields() {
      return this.selectedSuperType.fields;
    },
    availableTypes() {
      if (this.selectedSuperType) {
        return this.models.types[this.selectedSuperType.short_name];
      }
      return null;
    },
    availableSuperTypes() {
      return this.models.super_types;
    }
  },
};
</script>

<style scoped>
</style>
