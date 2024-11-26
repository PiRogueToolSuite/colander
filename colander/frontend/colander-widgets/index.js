import {vueComponent} from '../vues_components/vue-sub-component';
import EventEmitter from 'events';
import {Cache} from './cache';

let Event_System = new EventEmitter();
window.Colander = Object.assign(
    window.Colander || {},
    {Bus: Event_System, Cache: new Cache()});

let loc = window.location;
let ws_url_base = `ws://${loc.host}/ws-channel`;
let ws_url_case = `${ws_url_base}/global/`;
// let ws = new WebSocket(ws_url_case);
let ws = new WebSocket(`ws://${loc.host}${window.location.pathname}`);
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


jQuery(function ($) {
    //  Search toolbar
    let tbs = vueComponent('colander-toolbar-search');
    $('#toolbar-search').empty().append(tbs);
    //  Key-value pair table
    if ($('textarea#id_attributes').length > 0) {
        let hst = vueComponent('colander-hstore-table-edit');
        $('textarea#id_attributes').after(hst);
    }
});
