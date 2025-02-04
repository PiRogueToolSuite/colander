(()=>{"use strict";var __webpack_modules__={8523:(__unused_webpack_module,__webpack_exports__,__webpack_require__)=>{__webpack_require__.d(__webpack_exports__,{I:()=>vueComponent});let COMPONENT_TRACK_IDS={};async function async_load_component(destJContainer,component_name){let domResponse=await fetch(`/vues/${component_name}.vue`),dom=await domResponse.text();destJContainer.append(dom);let jsResponse=await fetch(`/vues/${component_name}.vue?part=js`),js=await jsResponse.text(),vueApp=eval(js);vueApp.config.errorHandler=(e,t,n)=>{console.warn(component_name,"app error",e,t,n)};let mountPoint=destJContainer.get(0),vueVm=vueApp.mount(mountPoint);return destJContainer.data("vue",vueVm),destJContainer.trigger("vue-ready",[destJContainer,vueVm]),`Vue component ready: ${component_name}`}const vueComponent=e=>{COMPONENT_TRACK_IDS[e]=COMPONENT_TRACK_IDS[e]||0,COMPONENT_TRACK_IDS[e]++;let t=$(`<div id='${e}-${COMPONENT_TRACK_IDS[e]}' class="vue-component"/>`);return async_load_component(t,e).then(console.log).catch(console.error),t}},7007:e=>{var t,n="object"==typeof Reflect?Reflect:null,r=n&&"function"==typeof n.apply?n.apply:function(e,t,n){return Function.prototype.apply.call(e,t,n)};t=n&&"function"==typeof n.ownKeys?n.ownKeys:Object.getOwnPropertySymbols?function(e){return Object.getOwnPropertyNames(e).concat(Object.getOwnPropertySymbols(e))}:function(e){return Object.getOwnPropertyNames(e)};var o=Number.isNaN||function(e){return e!=e};function i(){i.init.call(this)}e.exports=i,e.exports.once=function(e,t){return new Promise((function(n,r){function o(n){e.removeListener(t,i),r(n)}function i(){"function"==typeof e.removeListener&&e.removeListener("error",o),n([].slice.call(arguments))}d(e,t,i,{once:!0}),"error"!==t&&function(e,t){"function"==typeof e.on&&d(e,"error",t,{once:!0})}(e,o)}))},i.EventEmitter=i,i.prototype._events=void 0,i.prototype._eventsCount=0,i.prototype._maxListeners=void 0;var s=10;function a(e){if("function"!=typeof e)throw new TypeError('The "listener" argument must be of type Function. Received type '+typeof e)}function u(e){return void 0===e._maxListeners?i.defaultMaxListeners:e._maxListeners}function c(e,t,n,r){var o,i,s,c;if(a(n),void 0===(i=e._events)?(i=e._events=Object.create(null),e._eventsCount=0):(void 0!==i.newListener&&(e.emit("newListener",t,n.listener?n.listener:n),i=e._events),s=i[t]),void 0===s)s=i[t]=n,++e._eventsCount;else if("function"==typeof s?s=i[t]=r?[n,s]:[s,n]:r?s.unshift(n):s.push(n),(o=u(e))>0&&s.length>o&&!s.warned){s.warned=!0;var _=new Error("Possible EventEmitter memory leak detected. "+s.length+" "+String(t)+" listeners added. Use emitter.setMaxListeners() to increase limit");_.name="MaxListenersExceededWarning",_.emitter=e,_.type=t,_.count=s.length,c=_,console&&console.warn&&console.warn(c)}return e}function _(){if(!this.fired)return this.target.removeListener(this.type,this.wrapFn),this.fired=!0,0===arguments.length?this.listener.call(this.target):this.listener.apply(this.target,arguments)}function p(e,t,n){var r={fired:!1,wrapFn:void 0,target:e,type:t,listener:n},o=_.bind(r);return o.listener=n,r.wrapFn=o,o}function l(e,t,n){var r=e._events;if(void 0===r)return[];var o=r[t];return void 0===o?[]:"function"==typeof o?n?[o.listener||o]:[o]:n?function(e){for(var t=new Array(e.length),n=0;n<t.length;++n)t[n]=e[n].listener||e[n];return t}(o):v(o,o.length)}function f(e){var t=this._events;if(void 0!==t){var n=t[e];if("function"==typeof n)return 1;if(void 0!==n)return n.length}return 0}function v(e,t){for(var n=new Array(t),r=0;r<t;++r)n[r]=e[r];return n}function d(e,t,n,r){if("function"==typeof e.on)r.once?e.once(t,n):e.on(t,n);else{if("function"!=typeof e.addEventListener)throw new TypeError('The "emitter" argument must be of type EventEmitter. Received type '+typeof e);e.addEventListener(t,(function o(i){r.once&&e.removeEventListener(t,o),n(i)}))}}Object.defineProperty(i,"defaultMaxListeners",{enumerable:!0,get:function(){return s},set:function(e){if("number"!=typeof e||e<0||o(e))throw new RangeError('The value of "defaultMaxListeners" is out of range. It must be a non-negative number. Received '+e+".");s=e}}),i.init=function(){void 0!==this._events&&this._events!==Object.getPrototypeOf(this)._events||(this._events=Object.create(null),this._eventsCount=0),this._maxListeners=this._maxListeners||void 0},i.prototype.setMaxListeners=function(e){if("number"!=typeof e||e<0||o(e))throw new RangeError('The value of "n" is out of range. It must be a non-negative number. Received '+e+".");return this._maxListeners=e,this},i.prototype.getMaxListeners=function(){return u(this)},i.prototype.emit=function(e){for(var t=[],n=1;n<arguments.length;n++)t.push(arguments[n]);var o="error"===e,i=this._events;if(void 0!==i)o=o&&void 0===i.error;else if(!o)return!1;if(o){var s;if(t.length>0&&(s=t[0]),s instanceof Error)throw s;var a=new Error("Unhandled error."+(s?" ("+s.message+")":""));throw a.context=s,a}var u=i[e];if(void 0===u)return!1;if("function"==typeof u)r(u,this,t);else{var c=u.length,_=v(u,c);for(n=0;n<c;++n)r(_[n],this,t)}return!0},i.prototype.addListener=function(e,t){return c(this,e,t,!1)},i.prototype.on=i.prototype.addListener,i.prototype.prependListener=function(e,t){return c(this,e,t,!0)},i.prototype.once=function(e,t){return a(t),this.on(e,p(this,e,t)),this},i.prototype.prependOnceListener=function(e,t){return a(t),this.prependListener(e,p(this,e,t)),this},i.prototype.removeListener=function(e,t){var n,r,o,i,s;if(a(t),void 0===(r=this._events))return this;if(void 0===(n=r[e]))return this;if(n===t||n.listener===t)0==--this._eventsCount?this._events=Object.create(null):(delete r[e],r.removeListener&&this.emit("removeListener",e,n.listener||t));else if("function"!=typeof n){for(o=-1,i=n.length-1;i>=0;i--)if(n[i]===t||n[i].listener===t){s=n[i].listener,o=i;break}if(o<0)return this;0===o?n.shift():function(e,t){for(;t+1<e.length;t++)e[t]=e[t+1];e.pop()}(n,o),1===n.length&&(r[e]=n[0]),void 0!==r.removeListener&&this.emit("removeListener",e,s||t)}return this},i.prototype.off=i.prototype.removeListener,i.prototype.removeAllListeners=function(e){var t,n,r;if(void 0===(n=this._events))return this;if(void 0===n.removeListener)return 0===arguments.length?(this._events=Object.create(null),this._eventsCount=0):void 0!==n[e]&&(0==--this._eventsCount?this._events=Object.create(null):delete n[e]),this;if(0===arguments.length){var o,i=Object.keys(n);for(r=0;r<i.length;++r)"removeListener"!==(o=i[r])&&this.removeAllListeners(o);return this.removeAllListeners("removeListener"),this._events=Object.create(null),this._eventsCount=0,this}if("function"==typeof(t=n[e]))this.removeListener(e,t);else if(void 0!==t)for(r=t.length-1;r>=0;r--)this.removeListener(e,t[r]);return this},i.prototype.listeners=function(e){return l(this,e,!0)},i.prototype.rawListeners=function(e){return l(this,e,!1)},i.listenerCount=function(e,t){return"function"==typeof e.listenerCount?e.listenerCount(t):f.call(e,t)},i.prototype.listenerCount=f,i.prototype.eventNames=function(){return this._eventsCount>0?t(this._events):[]}}},__webpack_module_cache__={};function __webpack_require__(e){var t=__webpack_module_cache__[e];if(void 0!==t)return t.exports;var n=__webpack_module_cache__[e]={exports:{}};return __webpack_modules__[e](n,n.exports,__webpack_require__),n.exports}__webpack_require__.n=e=>{var t=e&&e.__esModule?()=>e.default:()=>e;return __webpack_require__.d(t,{a:t}),t},__webpack_require__.d=(e,t)=>{for(var n in t)__webpack_require__.o(t,n)&&!__webpack_require__.o(e,n)&&Object.defineProperty(e,n,{enumerable:!0,get:t[n]})},__webpack_require__.o=(e,t)=>Object.prototype.hasOwnProperty.call(e,t);var __webpack_exports__={},vue_sub_component=__webpack_require__(8523),events=__webpack_require__(7007),events_default=__webpack_require__.n(events);class Cache{#e={};constructor(){}store(e,t,n){return this.#e[e]=this.#e[e]||{},this.#e[e][t]=n}contains(e,t){return e in this.#e&&t in this.#e[e]}get(e,t){return this.#e[e]?.[t]}}let Event_System=new(events_default());window.Colander=Object.assign(window.Colander||{},{Bus:Event_System,Cache:new Cache});let loc=window.location,ws_protocol="ws:";loc.protocol.startsWith("https")&&(ws_protocol="wss:");let ws_url_base=null,ws_url_case=null,ws=new WebSocket(`${ws_protocol}//${loc.host}${loc.pathname}`);ws.addEventListener("message",(function(e){let t=JSON.parse(e.data);console.log("message data",t)})),ws.addEventListener("close",(function(e){console.log("close",arguments)})),ws.addEventListener("open",(function(e){console.log("open",arguments)})),ws.addEventListener("error",(function(e){console.log("error",arguments)})),Event_System.on("chat",(e=>{ws.send(JSON.stringify(e))})),jQuery((function(e){let t=(0,vue_sub_component.I)("colander-toolbar-search");if(e("#toolbar-search").empty().append(t),e("textarea#id_attributes").length>0){let t=(0,vue_sub_component.I)("colander-hstore-table-edit");e("textarea#id_attributes").after(t)}}))})();