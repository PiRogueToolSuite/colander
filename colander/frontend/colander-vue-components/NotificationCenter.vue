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
      opened: false,
      notifications: [],
      lastNotification: null,
    };
  },
  ready() {
    this.$logger(this, 'NotificationCenter');
  },
  mounted() {
    this.$bus.on('notification', this.onNotification);
    document.addEventListener('click', (evt) => {
      if (!evt.target.closest('#notification-center')) {
        this.close();
      }
    });
  },
  methods: {
    onNotification(notification) {
      let notif = Object.assign({id: new Date().getTime()}, notification);
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
      <Message v-if="lastNotification" severity="info" life="10000" @lifeEnd="dismissLastNotification()">
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
    margin: 1rem;
    box-shadow: 0 0 1rem white;
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
