import EventEmitter from 'events';
import {Cache} from './cache';

let Event_System = new EventEmitter();
window.Colander = Object.assign(
    window.Colander || {},
    {Bus: Event_System, Cache: new Cache()});

import ColanderBoot from '../colander';

function install_colander($) {
  ColanderBoot();
}

jQuery(function ($) {
  // --
  install_colander($);
  // --
});
