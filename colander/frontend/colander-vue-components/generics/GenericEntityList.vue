<template>
  <div class="generic-entity-list">
    <div v-if="!this.success">
      Unable to load data
    </div>
    <div v-else class="row">
      <div class="col-12">
        <Toolbar class="sticky-top">
          <template #start>
            <slot name="toolbarStart" :feed="this.feed">
            </slot>
          </template>
          <template #center v-if="!this.renderMode || this.renderMode === 'card'">
            <slot name="toolbarCenter" :feed="this.feed">
              <IconField>
                <InputIcon>
                  <i class="pi pi-search"/>
                </InputIcon>
                <InputText
                  placeholder="Search"
                  @valueChange="searchByEntityName($event)"
                  variant="filled"
                  type="search"
                  class="w-50"
                />
              </IconField>
            </slot>
          </template>
          <template #end>
            <slot name="toolbarEnd" :feed="this.feed">
            </slot>
          </template>
        </Toolbar>
        <div v-if="!this.loading && this.success && this.entities">
          <div v-if="!this.renderMode || this.renderMode === 'card'">
            <GenericEntity
              ref="entityList"
              v-for="entity in this.entities"
              :entity="entity"
              :key="entity.id"
              @select="onSelect(entity)"
              selectable
            >
              <template #right="slotProps">
                <slot name="right" :entity="entity" :feed="this.feed">
                </slot>
              </template>
            </GenericEntity>
          </div>
          <div v-else>
            <EntityQuickViewDialog ref="quickViewDialog" :entity="this.entityToView"/>
            <DataTable
              :value="this.entities"
              removableSort resizableColumns columnResizeMode="fit" rowHover
              @row-click="onSelect($event.data)"
              class="mt-3"
              :pt="{
                column: ({ props, context, parent }) => ({
                  bodycell: {
                    style: this.rowStyle(props, context, parent)
                  }
                })
              }"
            >
              <Column field="name" header="Name" ref="entityList">
                <template #body="slotProps">
                  <i class="fa me-1" :class="slotProps.data.superTypeStyle['icon-font-classname']"></i>
                  <Pills :entity="slotProps.data"/>
                  <i class="nf me-1" :class="slotProps.data.type['icon-font-classname']"></i>
                  <span class="font-monospace me-1 fw-bold text-truncate">{{ slotProps.data.name }}</span>
                  <Button icon="pi pi-eye" variant="text" size="small" rounded aria-label="Quick view"
                          @click="toggleQuickView($event, slotProps.data)"/>
                </template>
              </Column>
              <Column field="super_type.short_name" header="Type" sortable>
                <template #body="slotProps">
                  <span class="text-muted text-capitalize">{{ slotProps.data.super_type.name }} - </span>
                  <span class="text-muted fst-italic">{{ slotProps.data.type.name }}</span>
                </template>
              </Column>
              <Column header="">
                <template #body="slotProps">
                  <div class="d-flex align-self-stretch align-items-end justify-content-end">
                    <slot name="right" :entity="slotProps.data" :feed="this.feed">
                      <Button icon="pi pi-eye" size="small" label="Quick view"
                              @click="toggleQuickView($event, slotProps.data)"/>
                    </slot>
                  </div>
                </template>
              </Column>
            </DataTable>

          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Badge from "primevue/badge";
import Button from "primevue/button";
import ButtonGroup from "primevue/buttongroup";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import IconField from "primevue/iconfield";
import InputIcon from "primevue/inputicon";
import InputText from "primevue/inputtext";
import Toolbar from "primevue/toolbar";
import GenericEntity from "./GenericEntity.vue";
import Pills from "./Pills.vue";
import EntityQuickViewDialog from "./EntityQuickViewDialog.vue";

export default {
  props: {
    dataSource: String,
    renderMode: String,
  },
  components: {
    EntityQuickViewDialog,
    Badge, Button, Column, Toolbar, ButtonGroup, IconField, InputIcon, InputText, DataTable,
    GenericEntity, Pills,
  },
  data() {
    return {
      feed: null,
      selectedEntities: new Set(),
      entityToView: null,
      loading: true,
    }
  },
  created() {
    if (this.dataSource) {
      this.getData();
    }
  },
  methods: {
    async getData() {
      try {
        const response = await fetch(this.dataSource);
        if (!response.ok) {
          throw new Error(`Response status: ${response.status}`);
        }
        this.feed = await response.json();
        if (!this.success) {
          throw new Error("Unable to load data");
        }
        this.$themeUtils.attachStyleToEntities(this.entities).then(() => {
          this.loading = false;
        });
      } catch (error) {
        this.loading = false;
        this.$toast.add({severity: "error", summary: "Failed", detail: error.message, life: 3000});
      }
    },
    onSelect(entity) {
      if (!this.selectedEntities.has(entity.id)) {
        this.selectedEntities.add(entity.id);
      } else {
        this.selectedEntities.delete(entity.id);
      }
    },
    searchByEntityName(event) {
      const term = event;
      if (!term) {
        this.showAll();
      }
      this.$refs.entityList.forEach(
        (entity) => {
          if (entity.matchEntityName(term)) {
            entity.visible()
          } else {
            entity.hide();
          }
        }
      );
    },
    toggleQuickView(event, entity) {
      this.entityToView = entity;
      this.$refs.quickViewDialog.show();
      event.stopPropagation();
    },
    showAll() {
      this.$refs.entityList.forEach((entity) => {
        entity.visible();
      });
    },
    selectAll() {
      this.$refs.entityList.forEach((entity) => {
        entity.select();
      });
    },
    deselectAll() {
      this.$refs.entityList.forEach((entity) => {
        entity.deselect();
      });
    },
    getSelectedEntities() {
      return this.entities.filter((entity) => this.selectedEntities.has(entity.id));
    },
    rowStyle(props, context, parent) {
      const entity = parent.props.rowData;
      let s = {
        padding: '4px'
      }
      if (props?.field === "name" && entity?.superTypeStyle) {
        s.borderLeftWidth = '6px';
        s.borderLeftColor = entity.superTypeStyle.color;
        if (this.selectedEntities.has(entity.id)) {
          s.color = 'var(--bs-primary)';
          s.borderLeftColor = 'var(--bs-primary)';
        }
      }
      return s
    },
  },
  computed: {
    selectedEntitiesCount() {
      return this.selectedEntities.size;
    },
    allEntitiesCount() {
      return this.entities.length;
    },
    success() {
      if (this.feed) {
        return Object.hasOwn(this.feed, "entities");
      }
      return false;
    },
    entities() {
      if (this.success && this.feed) {
        return Object.values(this.feed.entities);
      } else {
        return [];
      }
    },
    entityTypes() {
      let entityTypes = {};
      if (this.success) {
        this.entities.forEach(entity => {
          const super_type = entity.super_type;
          const type = entity.type;
          const super_type_name = super_type.short_name;
          if (!Object.hasOwn(entityTypes, super_type_name)) {
            entityTypes[super_type_name] = {
              super_type: super_type,
              types: new Set()
            }
          }
          entityTypes[super_type_name].types.add(type);
        })
      }
      return entityTypes;
    },
  }
}
</script>

<style scoped>
.p-inputtext {
  min-width: 25vw;
}
</style>
