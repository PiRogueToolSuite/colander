import cytoscape from 'cytoscape';
import _ from 'lodash';
import contextMenus from 'cytoscape-context-menus';
import edgehandles from 'cytoscape-edgehandles';
import fcose from 'cytoscape-fcose';
import layoutUtilities from 'cytoscape-layout-utilities';
import {icons, icon_unicodes, color_scheme, shapes, base_styles} from './default-style';
import {overlay_button} from './graph-templates';
import {vueComponent} from '../vues_components/vue-sub-component';

// For sub-vue access
import MarkdownIt from 'markdown-it';
window.Markdown = new MarkdownIt({breaks:true});

cytoscape.use( contextMenus );
cytoscape.use( edgehandles );
cytoscape.use( layoutUtilities ); // Optional but used by fcose in our case
cytoscape.use( fcose );

let styles = [];

let node_label = _.memoize(function(e, iid) {
  let svgTxt = `${icon_unicodes[iid]} ${e.data('name')}`;

  const ctx = document.createElement('canvas').getContext("2d");
  const fStyle = e.style('font-style').strValue;
  const size = e.style('font-size').pfValue + 'px';
  const family = e.style('font-family').strValue;
  const weight = e.style('font-weight').strValue;
  ctx.font = fStyle + ' ' + weight + ' ' + size + ' ' + family;
  let measures = ctx.measureText(svgTxt);
  let maxWidth = measures.width + 8;

  if (e.data('type')) {
    let typeTxt = e.cy().data('all-styles')[e.data('super_type')].types[e.data('type')].name;
    measures = ctx.measureText(`${typeTxt}    `); // UGLY ? Fake multiple space (4) to have same padding
    maxWidth = Math.max(maxWidth, measures.width);
    svgTxt += `\n${typeTxt}`;
  }

  // A bit of margin:
  //maxWidth += 5;

  let r = { svgTxt: svgTxt, width: maxWidth };
  return r;
},(e) => {
  return `${e.id()}-${e.data('name')}-${e.data('type')}`;
});

styles.push({
  selector: 'node',
  style: {
    'background-blacken': -0.5,
    'shape': 'round-rectangle',
    'border-width': 3,
    'font-family': 'sans-serif, ForkAwesome',
    'font-size': '10px',
    'text-halign': 'center',
    'text-valign': 'center',
    'text-wrap': 'wrap',
  }
});

for(let iid in icons) {
  styles.push({
    selector: `node.${iid}`,
    style: {
      'background-color': color_scheme[iid],
      'border-color': color_scheme[iid],
      'label': (e)=> { return node_label(e, iid).svgTxt; },
      'width': (e) => { return node_label(e, iid).width; },
    }
  });
}

styles.push({
  selector: `node:selected`,
  style: {
    'background-color': '#7122da',
    'border-color': '#7122da',
    'background-blacken': 0,
    'color': 'white',
  }
});

styles.push({
  selector: 'edge',
  style: {
    'target-arrow-shape': 'vee',
    'width': 1,
    'label': 'data(name)',
    'text-halign': 'center',
    'text-valign': 'center',
    'text-outline-color': 'white',
    'text-outline-opacity': 1,
    'text-outline-width': 3,
    'font-family': 'sans-serif, ForkAwesome',
    'font-size': '10px',
    'curve-style': 'bezier',
    'loop-direction': '0deg',
    'loop-sweep': '-45deg',
    //'line-style': 'dashed',
  }
});

styles.push({
  selector: `edge:selected`,
  style: {
    'line-color': '#7122da',
    'color': '#7122da',
    'target-arrow-color': '#7122da',
  }
});

styles.push({
  selector: 'edge.eh-ghost-edge',
  style: {
    'label': '',
    'color': '#7122da',
    'line-color': '#7122da',
    'target-arrow-color': '#7122da',
    'line-style': 'dashed',
  }
});

styles.push({
  selector: 'edge[temporary]',
  style: {
    'color': '#7122da',
    'line-color': '#7122da',
    'target-arrow-color': '#7122da',
    'line-style': 'dashed',
  }
});


styles.push({
  selector: 'edge.immutable',
  style: {
    //'color': 'purple',
    'label': (ele) => { return `\uf023 ${ele.data('name')}`;}
    //'text-outline-color': 'red',
  }
});

class ColanderDGraph {
  // Attributes
  jRootElement;
  cy;
  g;
  jOverlayMenu;
  _config;
  constructor(config) {

    this.config( config || {} );

    this._domSetup();

    fetch('/rest/dataset/all_styles/')
      .then((r) => r.json())
      .then(this._onStyleFetched.bind(this))
      .catch(console.error);
  }

  _domSetup() {
    this.jRootElement = $(`#${this._config.containerId}`);
    this.jRootElement.addClass('colander-dgraph');

    // Encapsulate a sub-container to prevent buttons and sidepane event chaos
    // when childing stuff to cytoscape root element
    this.jGraphElement = $(`<div class='graph-sub-container'/>`)
    this.jRootElement.append(this.jGraphElement);

    this.jOverlayMenu = $(`<div class="graph-overlay-menu position-absolute top-0 start-0" style="z-index: 20;">`);
    this.jRootElement.append(this.jOverlayMenu);

    this.jLoading = $(`<div class="graph-loading">
        <div class="spinner-border" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
    </div>`);
    this.jRootElement.append(this.jLoading);
  }

  _onStyleFetched(allStyles) {

    this.allStyles = allStyles;

    this.cy = cytoscape({
      container: this.jGraphElement,
      userZoomingEnabled: true,
      userPanningEnabled: true,
      boxSelectionEnabled: true,
      wheelSensitivity: 0.5,
      style: styles,
      ready: this._onCyReady.bind(this)
    });

    this.cy.data('all-styles', this.allStyles);

    this.fixedPosition = {};

    this.cy.on('layoutstop', () => {
      this.jLoading.hide();
    });

    this._applyInternalConfig();
  }

  _scheduleOverridesSave() {
    if (this._HANDLER_OVERRIDE_SAVE) {
      clearTimeout( this._HANDLER_OVERRIDE_SAVE );
    }
    this._HANDLER_OVERRIDE_SAVE = setTimeout( this._overrideSave.bind(this), 1000 );
  }

  async _overrideSave() {

    if (this._HANDLING_SAVE_IN_PROGRESS) {
      // We already are in saving process
      // But it seems to take some time
      // memoize to do it again
      this._SCHEDULE_SAVE_AGAIN = true;
      return;
    }

    this._HANDLING_SAVE_IN_PROGRESS = true;
    if (this.jStatusSaving) this.jStatusSaving.show();

    let post_data = {};
    for(let nid in this.fixedPosition) {
      post_data[nid] = {
        position: this.fixedPosition[nid].position
      };
    }
    try {
      const rawResponse = await fetch(this._config.datasourceUrl, {
        method: 'PATCH',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'X-CSRFToken': this._config.csrfToken,
        },
        body: JSON.stringify(post_data),
      });
    } catch(e) {
      console.error("Unable to save overrides", e);
    }

    if (this._SCHEDULE_SAVE_AGAIN) {
      this._scheduleOverridesSave();
      delete this._SCHEDULE_SAVE_AGAIN;
    }

    if (this.jStatusSaving) this.jStatusSaving.hide();
    delete this._HANDLING_SAVE_IN_PROGRESS;
  }

  _onCyReady() {
    console.log('Fetching ...');
    fetch(this._config.datasourceUrl)
      .then((r) => r.json())
      .then(this._onGraphData.bind(this))
      .catch((e) => {
        console.error('Fetch error', e);
      });
  }

  _onGraphData(data) {
    this.g = data;
    for(let eid in this.g.entities) {
      let n = this._toNode(eid);
      this.cy.add(n);
    }
    for(let rid in this.g.relations) {
      let e = this._toEdge(rid);
      this.cy.add(e);
    }
    if (this.g.overrides) {
      // This part is strongly dependent to the layout engine used
      // In our case (for now), it's fcose
      for(let nid in this.g.overrides) {
        // Check if an override is still in current entities ecosystem.
        // If not, cytoscape override system does not support unknown 'override'
        // "delete"s any override no more relevant (by omitting it in referenced fixedPotitions).
        if (nid in this.g.entities === false) continue;
        this.fixedPosition[nid] = {
          nodeId: nid,
          position: this.g.overrides[nid].position,
        }
      }
    }

    if (this._sidepane_entities_overview) {
      let vue = this._sidepane_entities_overview.data('vue');
      // Workaround a race condition between graph data coming and sub-vue-component inited.
      if (vue) vue.entities = this.g.entities;
    }

    this.refreshGraph();
  }

  _createRelation(event, sourceNode, targetNode, addedEdge) {
    let ctx = {
      name: addedEdge.data('name'),
      obj_from: sourceNode.id(),
      obj_to: targetNode.id(),
      pending_edge: addedEdge,
    };
    this._create_or_rename_relation(ctx);
  }

  _renameRelation(renamedEdge) {
    let ctx = {
      id: renamedEdge.id(),
      name: renamedEdge.data('name'),
      pending_edge: renamedEdge,
    };
    this._create_or_rename_relation(ctx);
  }

  _create_or_rename_relation(ctx) {
    this._sidepane_relation_create_or_edit.data('vue').edit_relation(ctx);
    this.sidepane( this._sidepane_relation_create_or_edit );
  }

  async _do_createOrRenameRelation(ctx) {

    ctx.name = ctx.name?.trim();

    if (!ctx.name) {
      throw new Error('Empty relation name');
    }

    let post_data = Object.assign({}, ctx);
    delete post_data.pending_edge;

    const rawResponse = await fetch(
      ctx.id ? `/rest/entity_relation/${ctx.id}/` : '/rest/entity_relation/', {
      method: ctx.id ? 'PATCH':'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-CSRFToken': this._config.csrfToken,
      },
      body: JSON.stringify(post_data),
    });

    if (!rawResponse.ok) {
      throw new Error('Unexcpeted server error');
    }


    if (ctx.id) {
      // It's a rename
      ctx.pending_edge.data('name', ctx.name);
    }
    else {
      // It's a creation
      const content = await rawResponse.json();
      this.g.relations[content['id']] = content;
      let newEdge = this._toEdge(content['id']);
      this.cy.add(newEdge);
    }
  }

  async _deleteRelation(edge) {
    const rawResponse = await fetch(`/rest/entity_relation/${edge.id()}/`, {
      method: 'DELETE',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-CSRFToken': this._config.csrfToken,
      },
      body: JSON.stringify({})
    });

    if (!rawResponse.ok) {
      alert('Unexcpeted server error');
      return;
    }

    this.cy.remove(edge);
  }

  _createEntity(type, position) {
    let ctx = {
      super_type: type,
      name: 'New entity',
      position: position,
    };
    this._createOrEditEntity(ctx);
  }
  _createOrEditEntity(ctx) {

    /*
    let view = entity_creation_view(ctx, this.allStyles);
    view.find('button[role=save]').click(() => {
      ctx.name = view.find('input[name=name]').val();
      ctx.type = view.find('select[name=type]').val();
      ctx.content = view.find('textarea[name=content]').val();
      this._validate_createOrEditEntity(ctx)
          .then(this._do_createOrEditEntity.bind(this))
          .finally(this._cancelCreation.bind(this, ctx));
    });
    view.find('button[role=cancel]').click(this._cancelCreation.bind(this, ctx));
    this.sidePaneContent( view );
    view.find('input[name=name]').select();
     */
    this._sidepane_entity_create_or_edit.data('vue').edit_entity(ctx);
    this.sidepane(  this._sidepane_entity_create_or_edit );
  }

  _quickEditEntity(node) {
    let ctx = {
      //edited_node: node, // due to internal structure of a cy node,
                           // passing this kind of value to vue makes vue
                           // hangs forever in instrumenting 'edited_node' attribute
      id: node.id(),
      type: node.data('type'),
      name: node.data('name'),
      super_type: node.data('super_type'),
      content: node.data('content'),
    };
    this._createOrEditEntity(ctx);
  }

  async _do_createOrEditEntity(ctx) {
    let post_data = Object.assign({}, ctx);
    delete post_data.position;

    const rawResponse = await fetch(
        ctx.id?`/rest/entity/${ctx.id}/`:'/rest/entity/',
        {
          method: ctx.id ? 'PATCH' : 'POST',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-CSRFToken': this._config.csrfToken,
          },
          body: JSON.stringify(post_data),
    });

    if (!rawResponse.ok) {
      throw new Error('Unexcpeted server error');
    }

    const content = await rawResponse.json();

    this.g.entities[content['id']] = content;

    if (ctx.id) {
      // Edit
      let edited_node = this.cy.$(`#${ctx.id}`);
      edited_node.data('name', content.name);
      edited_node.data('content', content.content);
      edited_node.data('type', content.type);
    }
    else {
      // Create
      let newNode = this._toNode(content['id']);
      this.cy.add(newNode).position(ctx.position).emit('free');

      if (this._sidepane_entities_overview) {
        this._sidepane_entities_overview.data('vue').track_new_entity(content);
      }
    }

    if (this._sidepane_entities_overview) {
      this._sidepane_entities_overview.data('vue').refresh();
    }

  }

  async _viewDetail(node) {
    const rawResponse = await fetch(`/rest/entity/${node.id()}/`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-CSRFToken': this._config.csrfToken,
      }
    });

    if (!rawResponse.ok) {
      alert('Unexpected server error');
      return;
    }

    const content = await rawResponse.json();
    this._sidepane_entity_overview.data('vue').entity = content;
    this.sidepane(this._sidepane_entity_overview);
  }

  _toEdge(rid) {
    let r = Object.assign({}, this.g.relations[rid]);
    r.source = r.obj_from;
    r.target = r.obj_to;
    return {
      group: 'edges',
      data: r,
      classes: r['immutable'] ? ['immutable'] : ['mutable'],
    };
  }

  _toNode(eid) {
    let e = Object.assign({}, this.g.entities[eid]);
    return {
      group: 'nodes',
      data: e,
      classes: [ `${e.super_type}`, `${e.tlp}`, `${e.pap}` ]
    };
  }

  config(options) {
    this._config = Object.assign(this._config || {}, options);

    if (!this._config.containerId) throw new Error('ColanderDGraph; Missing containerId in config');
    if (!this._config.datasourceUrl) throw new Error('ColanderDGraph; Missing datasourceUrl in config');
  }

  _applyInternalConfig() {

    this.cy.userZoomingEnabled(!this._config.lock);
    this.cy.userPanningEnabled(!this._config.lock);
    this.cy.boxSelectionEnabled(!this._config.lock);

    if ( this._config.lock )
    {
      this.cy.style().selector('*').style({
        'events': 'no'
      });
      return false;
    }

    //
    // Overrides related stuff
    this.cy.on('layoutstop', () => {
      this.cy.$('node').emit('free');
    });

    this.cy.on('free', 'node', (e) => {
      let ele = e.target;
      this.fixedPosition[ ele.id() ] = this.fixedPosition[ ele.id() ] || { nodeId: ele.id() };
      this.fixedPosition[ ele.id() ].position = ele.position();
      this._scheduleOverridesSave();
    });

    if (!this.jStatusBar) {
      this.jStatusBar = $(`<div class='status-bar'></div>`);
      this.jStatusSaving = $(`<span class='status-saving' style="display: none;">
            <i class="fa fa-save"></i>
            <span>Saving ...</span>
        </span>`);
      this.jStatusBar.append(this.jStatusSaving);
      this.jRootElement.append(this.jStatusBar);
    }

    //
    // -- Edge (creation) handling plugin
    if (!this.edgeHandler) {
      this.edgeHandler = this.cy.edgehandles({
        canConnect: function (sourceNode, targetNode) {
          //return !sourceNode.same(targetNode); // disallow loops
          return true; // allow loops
        },
        edgeParams: (sourceNode, targetNode) => {
          // Temporary set the new edge name
          // will be overridden by user with edge name prompt
          return {data: {name: 'New relation', temporary: true}};
        },
        snap: false,
      });
      this.cy.on('ehcomplete', this._createRelation.bind(this));
    }

    this.cy.on('dbltap', (e) => {
      let node = e.target;
      if (e.target === this.cy || e.target.isEdge()) {
        // Dbltap done on graph background
        //this.sidepane(false);
        if (this._sidepane_entities_overview) {
          this.sidepane(this._sidepane_entities_overview);
        }
      } else {
        // Dbltap done on a entity
        this._viewDetail(node)
            .then(console.log)
            .catch(console.error);
      }
    });

    //
    // -- Context menu (right-click) plugin
    if (!this.contextMenu) {
      this.contextMenu = this.cy.contextMenus({
        menuItems: [
          {
            id: 'relation-create',
            content: 'Create relation',
            tooltipText: 'Add relation between two entities',
            selector: 'node',
            image: {src: '/static/images/icons/link.svg', width: 12, height: 12, x: 4, y: 7},
            onClickFunction: (e) => {
              let node = e.target;
              this.edgeHandler.start(node);
            }
          },
          {
            id: 'relation-rename',
            content: 'Rename relation',
            tooltipText: 'Add relation between two entities',
            selector: 'edge.mutable',
            image: {src: '/static/images/icons/pencil-square-o.svg', width: 12, height: 12, x: 4, y: 7},
            onClickFunction: (e) => {
              let edge = e.target;
              this._renameRelation(edge);
            }
          },
          {
            id: 'relation-delete',
            content: 'Delete relation',
            tooltipText: 'Delete relation between two entities',
            selector: 'edge.mutable',
            image: {src: '/static/images/icons/trash.svg', width: 12, height: 12, x: 4, y: 7},
            onClickFunction: (e) => {
              let edge = e.target;
              this._deleteRelation(edge)
                  .then(console.log)
                  .catch(console.error);
            }
          },
          {
            id: 'entity-details',
            content: 'Entity overview',
            tooltipText: 'View entity details',
            selector: 'node',
            image: {src: '/static/images/icons/eye.svg', width: 12, height: 12, x: 4, y: 7},
            onClickFunction: (e) => {
              let node = e.target;
              this._viewDetail(node)
                .then(console.log)
                .catch(console.error);
            }
          },
          {
            id: 'entity-edit',
            content: 'Quick edit entity',
            tooltipText: 'Quick edit',
            selector: 'node',
            image: {src: '/static/images/icons/pencil-square-o.svg', width: 12, height: 12, x: 4, y: 7},
            onClickFunction: (e) => {
              let node = e.target;
              this._quickEditEntity(node);
              //window.location = node.data('absolute_url');
            }
          },
          {
            id: 'select-linked',
            content: 'Select linked',
            tooltipText: 'Select all linked entities',
            selector: 'node,edge',
            image: {src: '/static/images/icons/hubzilla.svg', width: 12, height: 12, x: 4, y: 7},
            onClickFunction: (e) => {
              let linked = ColanderDGraph.cy_linked(e.target);
              linked.select();
            }
          },
          {
            id: 'relax-linked',
            content: 'Relax linked',
            tooltipText: 'Relax all linked entities',
            selector: 'node',
            image: {src: '/static/images/icons/hubzilla.svg', width: 12, height: 12, x: 4, y: 7},
            onClickFunction: (e) => {
              let linked = ColanderDGraph.cy_linked(e.target);

              for(let ele of linked) {
                delete this.fixedPosition[ele.id()];
              }

              this.refreshGraph();
            }
          },
          {
            id: 'entity-create',
            content: 'New entity',
            tooltipText: 'Create a new entity',
            image: {src: '/static/images/icons/plus-circle.svg', width: 12, height: 12, x: 4, y: 7},
            coreAsWell: true,
            submenu: ['Actor', 'Device', 'Threat', 'Observable', 'DataFragment'].map((t) => ({
              id: `create-${t}`,
              content: `${t}`,
              tooltipText: `Create a new ${t} entity`,
              image: {src: `/static/images/icons/${t}.svg`, width: 12, height: 12, x: 4, y: 7},
              onClickFunction: (e) => {
                this._createEntity(t, e.position);
              }
            })),
          }
        ],

        submenuIndicator: {src: '/static/images/icons/caret-right.svg', width: 12, height: 12, x: 4, y: 4},
      });
    }
    // Full screen editor
    if (this._config.fullscreen && !this.jOverlayMenu_Fullscreen) {
      this.jOverlayMenu_Fullscreen = overlay_button('fa-arrows-alt', 'Fullscreen');
      this.jOverlayMenu_Fullscreen.click((e)=> {
        this.jRootElement.toggleClass('fullscreen');
      });
      this.jOverlayMenu.append(this.jOverlayMenu_Fullscreen);
    }
    // ReCenter and Fit graph
    if (this._config.recenter && !this.jOverlayMenu_Recenter) {
      this.jOverlayMenu_Recenter = overlay_button('fa-crosshairs', 'Re-Center');
      this.jOverlayMenu_Recenter.click((e)=> {
        e.stopPropagation();
        e.preventDefault();
        this.cy.fit();
      });
      this.jOverlayMenu.append(this.jOverlayMenu_Recenter);
    }
    // Snapshot
    if (this._config.snapshot && !this.jOverlayMenu_Snapshot) {
      this.jOverlayMenu_Snapshot = overlay_button('fa-picture-o', 'Export as PNG');
      this.jOverlayMenu_Snapshot.click((e)=> {
        e.stopPropagation();
        e.preventDefault();
        let png64 = this.cy.png({full:true, bg: 'white', scale: 2});
        let aPng = document.createElement('a');
        aPng.download = `${this.g.name}.png`;
        aPng.href = png64;
        aPng.click();
        /*
        let image = new Image();
        image.src = png64;
        let w = window.open("");
        w.document.write(image.outerHTML);
         */
      });
      this.jOverlayMenu.append(this.jOverlayMenu_Snapshot);
    }
    // Sidebar toggle
    if (this._config.sidepane && !this.jOverlayMenu_Sidepane) {
      this.jOverlayMenu_Sidepane = $(`<div class='sidepane'></div>`);
      this.jRootElement.append(this.jOverlayMenu_Sidepane);

      //
      // Resize stuff sidepane
      let resizing = false;
      let previous_screen_x = 0;
      let sidepane_width = 0;
      this.jRootElement.mousedown((e) => {
        resizing = e.offsetX < 5;
        if (resizing) {
          sidepane_width = this.jOverlayMenu_Sidepane.outerWidth();
          previous_screen_x = e.screenX;
          e.preventDefault();
          e.stopPropagation();
        }
      }).mousemove((e) => {
        if (!resizing) return;
        let delta = previous_screen_x - e.screenX;
        previous_screen_x = e.screenX;
        sidepane_width = Math.max(40, (sidepane_width + delta));
        this.jOverlayMenu_Sidepane.get(0).style.setProperty('--sidepane-width', `${sidepane_width}px`);
      }).mouseup((e) => {
        resizing = false;
      });
      // End: Resize stuff sidepane
      //

      this.sidepane = (t) => {
        // Current active (if one)
        if (typeof(t) === 'boolean') {
          this.jRootElement.toggleClass('sidepane-active', t);
        }
        if (typeof(t) === 'object') {
          this.jOverlayMenu_Sidepane.find('.vue-component').removeClass('active');
          t.addClass('active');
          this.jRootElement.toggleClass('sidepane-active', true);
        }
      };
      this.sidepane_add = (pane) => {
        this.jOverlayMenu_Sidepane.append(pane);
      };
      this.sidePaneContent = (c) => {
        this.jOverlayMenu_Sidepane.empty().append(c);
        this.sidepane(true);
      };
      // this.jOverlayMenu.append(this.jOverlayMenu_SidepaneButton);
    }

    setTimeout( this._init_vues.bind(this) );
  }
  static cy_linked(ele) {
    let selection = ele;
    if (selection.isEdge()) {
      selection = selection.connectedNodes()
    }
    let currentCount = selection.length;
    do {
      currentCount = selection.length
      selection = selection.closedNeighborhood();
    } while( currentCount < selection.length );
    return selection;
  }
  _init_vues() {

    //
    // Entities list
    // ========================================================================
    this._sidepane_entities_overview = vueComponent('colander-dgraph-entities-table');
    this.sidepane_add(this._sidepane_entities_overview);
    //this.jOverlayMenu_Sidepane.append(this._sidepane_entities_overview);
    this._sidepane_entities_overview.on('close-component', (e) => {
      this.sidepane(false);
    });
    this._sidepane_entities_overview.on('vue-ready', (e, jDom, vue) => {
      vue.allStyles = this.allStyles;
      if (this.g) {
        vue.entities = this.g.entities;
      }
    });
    this._sidepane_entities_overview.on('focus-entity', (e, eid) => {
      let pos = this.cy.$(`#${eid}`).position();

      this.cy.animate({
        center: { eles: this.cy.$(`#${eid}`) },
        zoom: 2,
        easing: 'ease-in-out',
        duration: 1500,
      });
    });

    //
    // Entity edit form
    // ========================================================================
    this._sidepane_entity_create_or_edit = vueComponent('colander-dgraph-entity-edit');
    this.sidepane_add(this._sidepane_entity_create_or_edit);
    this._sidepane_entity_create_or_edit.on('vue-ready', (e, jDom, vue) => {
      vue.allStyles = this.allStyles;
    });
    this._sidepane_entity_create_or_edit.on('close-component', (e) => {
      this.sidepane(false);
    });
    this._sidepane_entity_create_or_edit.on('save-entity', (e, entity) => {
      this._do_createOrEditEntity(entity)
        .then(console.log).catch(console.error);
      this.sidepane(false);
    });

    //
    // Relation edit form
    // ========================================================================
    this._sidepane_relation_create_or_edit = vueComponent('colander-dgraph-relation-edit');
    this.sidepane_add(this._sidepane_relation_create_or_edit);
    this._sidepane_relation_create_or_edit.on('vue-ready', (e, jDom, vue) => {
      vue.allStyles = this.allStyles;
    });
    this._sidepane_relation_create_or_edit.on('close-component', (e, ctx) => {
      this.sidepane(false);
      if (!ctx.id) {
        this.cy.remove(ctx.pending_edge);
      }
    });
    this._sidepane_relation_create_or_edit.on('save-relation', (e, ctx) => {
      this._do_createOrRenameRelation(ctx)
        .then(console.log).catch(console.error);
      this.sidepane(false);
      if (!ctx.id) {
        this.cy.remove(ctx.pending_edge);
      }
    });

    //
    // Entity overview / detail view
    // ========================================================================
    this._sidepane_entity_overview = vueComponent('colander-dgraph-entity-overview');
    this.sidepane_add(this._sidepane_entity_overview);
    this._sidepane_entity_overview.on('vue-ready',(e,jDom,vue) => {
      vue.allStyles = this.allStyles;
    });
    this._sidepane_entity_overview.on('close-component', (e) => {
      this.sidepane(false);
    });
    this._sidepane_entity_overview.on('quick-edit-entity', (e, eid) => {
      let tmp = JSON.parse(JSON.stringify(this.g.entities[eid]));
      this._sidepane_entity_create_or_edit.data('vue').edit_entity( tmp );
      this.sidepane(  this._sidepane_entity_create_or_edit );
    });
  }
  refreshGraph() {

    this.firstLayout = this.firstLayout === undefined;

    let ly = this.cy.layout({
      name: 'fcose',
      quality: 'proof',
      randomize: this.firstLayout,
      fit: this.firstLayout,
      animate: !this.firstLayout,
      animationDuration: 200,
      padding: 0,
      nodeDimensionsIncludeLabels: true,
      packComponents: true,
      numIter: 2500,
      gravity: 5,
      idealEdgeLength: (e) => {
        return 10*Math.max(5,e.data('name').length);
      },
      fixedNodeConstraint: Object.values(this.fixedPosition),
      initialEnergyOnIncremental: 0.5,
    }).run();
  }
}

window.ColanderDGraph = ColanderDGraph;
