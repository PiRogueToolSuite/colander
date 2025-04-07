import {vueComponent} from '../vues_components/vue-sub-component';
import EventEmitter from 'events';
import {Cache} from './cache';

let Event_System = new EventEmitter();
window.Colander = Object.assign(
    window.Colander || {},
    {Bus: Event_System, Cache: new Cache()});

let loc = window.location;
let ws_protocol = 'ws:';
if (loc.protocol.startsWith('https')) {
    ws_protocol = 'wss:';
}
let ws_url_base = `ws://${loc.host}/ws-channel`;
let ws_url_case = `${ws_url_base}/global/`;
// let ws = new WebSocket(ws_url_case);
let ws = new WebSocket(`${ws_protocol}//${loc.host}${loc.pathname}`);
ws.addEventListener('message', function(evt) {
   let data = JSON.parse(evt.data)
   console.log('message data', data);
});
ws.addEventListener('close', function(evt) {
   console.log('close', arguments);
});
ws.addEventListener('open', function(evt) {
   console.log('open', arguments);
});
ws.addEventListener('error', function(evt) {
   console.log('error', arguments);
});

Event_System.on('chat', (msg) => {
   ws.send(JSON.stringify(msg));
});

import ColanderBoot from '../colander';
import CTIF from '../vues_components/colander-thumbnail-input-field/colander-thumbnail-input-field.vue';
import { createApp } from 'vue';

function install_legacies($) {
  // Thumbnailer
  $('#div_id_thumbnail').each((idx, el) => {
    let app = createApp(CTIF);
    //console.log('app', app);
    const replacedJDom = $(el).clone(); // clone cause vue3 mount will 'replace' dom element content
    const instance = app.mount(el);
    instance.replacedDom?.(replacedJDom);
  });
}

function install_colander($) {
  ColanderBoot();
}

jQuery(function ($) {
  // --
  install_colander($);
  // --
  install_legacies($);
  //install_har($);
});
