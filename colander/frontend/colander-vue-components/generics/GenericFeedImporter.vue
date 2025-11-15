<template>
  <div class="generic-feed-importer">
    <CachedFileUpload
      :dataCaseId="this.dataCaseId"
      :dataCsrfToken="this.dataCsrfToken"
      :converter="this.feedType"
    >
      <template #next="slotProps">
        <Card v-if="slotProps.dataSource">
          <template #content>
            <GenericEntityList ref="entityList" :data-source="slotProps.dataSource" render-mode="card">
              <template #toolbarStart="slotProps">
                <ButtonGroup>
                  <Button severity="primary" label="Select all" @click="selectAll"/>
                  <Button severity="primary" label="Deselect all" @click="deselectAll"/>
                </ButtonGroup>
              </template>
              <template #toolbarEnd="slotProps">
                <ButtonGroup>
                  <Button
                    severity="primary"
                    label="Import selection"
                    :disabled="this.$refs.entityList.selectedEntitiesCount === 0"
                    @click="importSelection"
                    :badge="this.$refs.entityList.selectedEntitiesCount.toString()"
                  />
                  <Button
                    severity="primary"
                    label="Import whole feed"
                    :disabled="this.$refs.entityList.allEntitiesCount === 0"
                    :badge="this.$refs.entityList.allEntitiesCount.toString()"
                    @click="importAll"
                  />
                </ButtonGroup>
              </template>
<!--              <template #right="slotProps">-->
<!--                Add actions-->
<!--              </template>-->
            </GenericEntityList>
          </template>
        </Card>
      </template>
    </CachedFileUpload>
  </div>
</template>

<script>
import Button from "primevue/button";
import ButtonGroup from "primevue/buttongroup";
import Card from "primevue/card";
import CachedFileUpload from "../generics/CachedFileUpload.vue";
import GenericEntityList from "../generics/GenericEntityList.vue";

export default {
  props: {
    dataCaseId: String,
    dataCsrfToken: String,
    feedType: String,
  },
  components: {
    Button,
    ButtonGroup,
    Card,
    GenericEntityList,
    CachedFileUpload,
  },
  data() {
    return {
    }
  },
  methods: {
    selectAll() {
      this.$refs.entityList.selectAll();
    },
    deselectAll() {
      this.$refs.entityList.deselectAll();
    },
    importSelection() {
      const entitySelection = this.$refs.entityList.getSelectedEntities();
      const payload = {
        case_id: this.dataCaseId || null,
        entities: entitySelection,
      }
      $.ajax({
        type: 'POST',
        url: '/rest/feed/import_entities/',
        dataType: 'json',
        contentType: "application/json; charset=utf-8",
        data: JSON.stringify(payload),
        headers: {
          'X-CSRFToken': this.dataCsrfToken,
        },
        success: (response) => {
          this.$toast.add({severity: "success", summary: "Success", detail: response.message, life: 3000});
        },
        error: () => (response) => {
          this.$toast.add({severity: "error", summary: "Error", detail: response.message, life: 3000});
        }
      });
    },
    importAll() {
      const payload = {
        case_id: this.dataCaseId || null,
        feed: this.$refs.entityList.feed,
      }
      $.ajax({
        type: 'POST',
        url: '/rest/feed/import_feed/',
        dataType: 'json',
        contentType: "application/json; charset=utf-8",
        data: JSON.stringify(payload),
        headers: {
          'X-CSRFToken': this.dataCsrfToken,
        },
        success: (response) => {
          this.$toast.add({severity: "success", summary: "Success", detail: response.message, life: 3000});
        },
        error: (response) => {
          this.$toast.add({severity: "error", summary: "Error", detail: response.message, life: 3000});
        }
      });
    }
  }
}
</script>

<style scoped>
.p-card {
  background: #ececec;
}
</style>
