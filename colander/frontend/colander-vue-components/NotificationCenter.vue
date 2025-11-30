<script>
import Badge from "primevue/badge";
import {Message} from "primevue";

export default {
  components: {
    Badge,
    Message,
  },
  data() {
    return {
      loaded: false,
      opened: false,
      notifications: [],
      lastNotification: null,
    };
  },
  created() {
    this.$logger(this, 'NotificationCenter');
  },
  watch: {
    'notifications.length'(new_value, old_value) {
      if (!this.loaded) return;
      this.save();
    }
  },
  mounted() {
    this.$bus.on('notification', this.onNotification);
    document.addEventListener('click', (evt) => {
      if (!evt.target.closest('#notification-center')) {
        this.close();
      }
    });
    this.load();
  },
  methods: {
    load() {
      let existingNotifications = this.$localStorage.get('notifications', []);
      for(let n of existingNotifications) {
        this.notifications.push(n);
      }
      this.loaded = true;
      this.$debug('loaded');
    },
    save() {
      this.$localStorage.set('notifications', this.notifications);
      this.$debug('saved');
    },
    onNotification(notification) {
      let now = new Date().getTime();
      let idSuffix = (Math.random() + 1).toString(36).substring(7);
      let id = `${now}-${idSuffix}`;
      let notif = Object.assign({id: id, timestamp: now}, notification);
      this.notifications.splice(0, 0, notif);
      this.lastNotification = Object.assign({}, notif);
    },
    dismissLastNotification() {
      this.lastNotification = null;
    },
    toggle() {
      this.opened = !this.opened;
      if (this.opened) {
        this.dismissLastNotification();
      }
    },
    close() {
      this.opened = false;
    },
    ack(index) {
      this.$refs.toggleLink.focus();
      setTimeout(() => {
        this.notifications.splice(index, 1);
        if (!this.hasNotifications) {
          setTimeout(() => {
            this.close();
          }, 1000);
        }
      }, 500);
    },
  },
  computed: {
    maxSeverity() {
      return 'secondary';
    },
    notificationCount() {
      return this.notifications.length;
    },
    hasNotifications() {
      return this.notificationCount > 0;
    }
  }
}
</script>
<template>
  <div id="notification-center" class="nav-item position-relative">
    <a class="nav-link text-nowrap text-light position-relative activable"
       :class="{ active: opened }" href="#"
       @click="toggle()"
       ref="toggleLink">
        <i class="fa fa-envelope" aria-hidden="true"></i>
        <Badge v-if="hasNotifications" :value="notificationCount" :severity="maxSeverity" size="small" class="local-badge" />
    </a>
    <div class="notification-container">
      <Message v-if="lastNotification" severity="info" :life="3000" @lifeEnd="dismissLastNotification()" closable>
        <strong class="notification-msg">{{lastNotification.msg}}</strong>
        <div v-if="lastNotification.detail" class="notification-detail">{{lastNotification.detail}}</div>
      </Message>
    </div>
    <div class="notification-container notification-list" :class="{ opened: opened }">
      <div v-if="hasNotifications">
        <Message v-for="(notif, index) in notifications" :key="notif.id"
                 severity="info"
                 closable @close="ack(index)">
          <strong class="notification-msg">{{notif.msg}}</strong>
          <div v-if="notif.detail" class="notification-detail">{{notif.detail}}</div>
          <a v-if="notif.url" class="notification-url link-secondary" :href="notif.url">
            <i class="fa fa-eye"></i>
            Open
          </a>
        </Message>
      </div>
      <div v-else>
        <Message severity="secondary">No message</Message>
      </div>
    </div>
  </div>
</template>
<style>
a.activable.active
{
  background-color: var(--bs-light);
  --bs-light-rgb: --bs-primary-rgb;
  color: var(--bs-primary);
  &:hover {
    background-color: var(--bs-light);
  }
}
.local-badge {
  position: absolute;
  top: 0.25rem;
  right: 0.25rem;
}
.notification-container
{
  position: absolute;
  top: 3rem;
  right: 0;
  width: 400px;
  z-index: 10;

  .p-message {
    position: relative;
    margin: 1rem;
    box-shadow: 0 0 1rem white;
  }

  .p-message-close-button {
    position: absolute;
    right: 0.25rem;
    top: 0.25rem;
  }

  .notification-msg {}
  .notification-detail {}
}
.notification-list {
  background-color: white;
  box-shadow: 0 1rem 1.5rem -1rem rgba(0,0,0,0.5);
  overflow-x: hidden;
  overflow-y: auto;
  max-height: 0;
  transition: 0.5s;
  transition-property: width, max-height;
  &.opened {
    max-height: 50vh;
  }
  z-index: 20;
}
</style>
