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
              @change="this.sanityCheck"
              optionLabel="name"
              placeholder="Select entity type"
              class="mx-2"/>
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
            <ButtonGroup>
              <Button
                label="Reload"
                severity="primary"
                :disabled="!this.inputFile"
                icon="pi pi-refresh"
                @click="this.parseFile"/>
              <Button
                label="Import"
                severity="primary"
                :disabled="this.inError"
                icon="pi pi-cloud-upload"
                @click="this.import_data"
              />
              <Button
                label="Dump"
                severity="primary"
                :disabled="this.inError"
                @click="this.dump"/>
            </ButtonGroup>
          </template>
        </Toolbar>
      </div>
    </div>

    <div class="row mt-2">
      <div class="col-12">
        <Panel header="Map your CSV">
          <div v-if="error" class="p-error p-mt-2">
            {{ this.error }}
          </div>
          <div v-if="this.tableData.length === 0 && !this.loading" class="p-text-center p-mt-4 fw-bold text-warning">
            <p>Please select a CSV file, the first row of your file must contains the column names.</p>
          </div>
          <DataTable
            :value="this.tableData"
            :loading
            :rowClass="this.row_status"
            scrollable
            removableSort
            resizableColumns
            columnResizeMode="fit"
            size="small"
            v-if="this.tableData.length > 0"
          >
            <template #header v-if="this.tableData.length > 0">
              <div>Assign an entity property to the columns of your CSV.</div>
              <div class="row mt-2">
                <div class="col-md-6">
                  You are about to create {{ this.tableData.length }}
                  <i>{{ this.selectedSuperType.name }}</i> entities.
                  Available properties:
                  <ul>
                    <li v-for="field of this.availableFields">
                      <i class="pi pi-times me-1" style="color: var(--p-red-500)" v-if="field.mappingError"></i>
                      <i class="pi pi-check me-1" style="color: var(--p-lime-500)" v-else></i>
                      <span class="text-primary">{{ field.label }}</span>
                      (<span class="font-monospace fst-italic">{{ field.name }}</span>):
                      <span v-if="field.required" class="fw-bold">required, </span>
                      <span v-else class="fw-bold">optional, </span>
                      <span v-if="!field.multiple"> can be used only once</span>
                      <span v-else> can be used multiple times</span>
                      <span v-if="field.name==='ignored_field'"> to flag a column as ignored</span>
                    </li>
                  </ul>
                </div>
                <div class="col-md-6">
                  How your CSV will be imported:
                  <ul class="">
                    <li v-for="col of this.columns">
                      the column <span class="font-monospace text-primary">{{ col.header }}</span>
                      <span v-if="col.targetField && col.targetField.name!=='ignored_field'">
                        will set the property <span class="text-primary">{{ col.targetField.label }}</span>.
                      </span>
                      <span v-else>
                        will be ignored.
                      </span>
                    </li>
                  </ul>
                </div>
              </div>
              <div class="row mt-1">
                <div class="col-md-6">
                  Apply <i>{{ this.selectedSuperType.name }}</i> type to all rows: <Select
                  v-model="this.defaultType"
                  :options="this.availableTypes"
                  :loading
                  filter
                  optionLabel="name"
                  placeholder="Default type"
                  @valueChange="this.applyDefaultType"
                  class="me-2"/>
                </div>

                <div class="col-md-6">
                  Hide CSV columns:
                  <MultiSelect :modelValue="this.selectedColumns" :options="this.columns" optionLabel="header" :loading
                               @update:modelValue="this.onToggleColumn" display="chip" placeholder="Select Columns"/>
                </div>
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
                  placeholder="Select row type"
                  class=""/>
              </template>
            </Column>
            <Column
              v-for="(col, index) of this.selectedColumns"
              :sortable="true"
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
                    class="w-full" variant="filled"
                    size="small"
                    optionLabel="label"
                    placeholder="Select column type"
                    @valueChange="this.sanityCheck"/>
                  <label :for="col.field" class="font-monospace text-primary fw-bold">{{ col.header }}</label>
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
import ButtonGroup from "primevue/buttongroup";
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
  props: {
    dataCaseId: String,
    dataCsrfToken: String,
  },
  components: {
    Button,
    ButtonGroup,
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
      inError: true,
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
    row_status(data) {
      if (data.imported)
        return 'text-success';
      if (data.importFailed)
        return 'text-danger';
      return '';
    },
    import_data() {
      this.tableData.forEach((row) => {
        if (row.targetType !== null) {
          let entity = {
            case_id: this.dataCaseId || null,
            super_type: this.selectedSuperType.short_name,
            type: row.targetType.id,
            attributes: {},
          };
          this.columns.forEach((column) => {
            if (column.targetField != null && column.targetField.name !== "ignored_field") {
              const targetFieldName = column.targetField.name;
              const fieldName = column.field;
              const cellValue = row[fieldName];
              if (targetFieldName === "attributes" && cellValue) {
                entity.attributes[fieldName] = cellValue;
              } else if (cellValue) {
                entity[targetFieldName] = cellValue;
              }
            }
          });

          $.ajax({
            type: 'POST',
            url: '/rest/entity/',
            dataType: 'json',
            contentType: "application/json; charset=utf-8",
            data: JSON.stringify(entity),
            headers: {
              'X-CSRFToken': this.dataCsrfToken,
            },
            success: () => {
              row.imported = true;
            },
            error: () => {
              row.imported = false;
              row.importFailed = true;
            }
          });
        }
      });
    },
    sanityCheck() {
      if (this.dataCaseId === null) {
        return false;
      }
      let valid = this.tableData.length > 0;
      this.availableFields.forEach((f) => {
        f.mappingError = f.required;
        f.mappingCount = 0;
        this.columns.forEach((column) => {
          if (column.targetField && column.targetField.name === f.name) {
            f.mappingCount += 1;
            f.mappingError = false;
            if (f.mappingCount > 1 && !column.targetField.multiple) {
              f.mappingError = true;
              valid = false;
            }
          }
        });
        if (f.required && f.mappingCount === 0) {
          f.mappingError = true;
          valid = false
        }
      });
      this.inError = !valid;
      return valid;
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
      this.sanityCheck();

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
      this.selectedColumns = this.columns.filter(col => val.includes(col));
    },
    processParsedData(results, file) {
      this.tableData = results.data.map(row => ({
        ...row,
        targetType: null,
        exists: false,
        imported: false,
        importFailed: false,
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
.p-select {
  min-width: 140px;
}
</style>
