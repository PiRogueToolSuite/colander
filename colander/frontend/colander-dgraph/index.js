import cytoscape from 'cytoscape';
import _ from 'lodash';
import contextMenus from 'cytoscape-context-menus';
import edgehandles from 'cytoscape-edgehandles';
import fcose from 'cytoscape-fcose';
import layoutUtilities from 'cytoscape-layout-utilities';
import {icons, icon_unicodes, color_scheme, shapes, base_styles} from './default-style';
import {overlay_button, details_view, entity_creation_view, entity_relation_view} from './graph-templates';

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
    //let typeTxt = e.data('type');
    let typeTxt = e.cy().data('all-styles')[e.data('super_type')].types[e.data('type')].name;
    //console.log('all styles', e.cy().data('all-styles'));
    measures = ctx.measureText(`${typeTxt}    `); // UGLY ? Fake multiple space (4) to have same padding
    maxWidth = Math.max(maxWidth, measures.width);
    svgTxt += `\n${typeTxt}`;
  }

  // A bit of margin:
  //maxWidth += 5;

  let r = { svgTxt: svgTxt, width: maxWidth };
  //console.log('node_label', ctx.font, r);
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
        console.log('Fetch error', e);
      });
  }
  _onGraphData(data) {
    console.log('on graph data', data);
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
        this.fixedPosition[nid] = {
          nodeId: nid,
          position: this.g.overrides[nid].position,
        }
      }
    }

    this.refreshGraph();
  }
  _createRelation(event, sourceNode, targetNode, addedEdge) {
    //console.log('_createRelation', addedEdge.data('source'), addedEdge.data('name'), addedEdge.data('target'));
    let ctx = {
      name: addedEdge.data('name'),
      obj_from: sourceNode.id(),
      obj_to: targetNode.id(),
      pending_edge: addedEdge,
    };
    let view = entity_relation_view(ctx, this.allStyles);
    view.find('button[role=save]').click(() => {
      ctx.name = view.find('input[name="name"]').val();
      this._do_createRelation(ctx)
        .then(this._cancelRelation.bind(this, ctx, true))
        .catch(this._cancelRelation.bind(this, ctx, true));
    });
    view.find('button[role=cancel]').click(this._cancelRelation.bind(this, ctx, true));
    this.sidePaneContent( view );
    view.find('input[name="name"]').select();
  }
  _cancelRelation(ctx, removePending, error) {
    if (error) {
      console.error('Relation modification canceled', error);
    }
    this.sidepane(false);
    if (removePending) {
      this.cy.remove(ctx.pending_edge);
    }
  }
  async _do_createRelation(ctx) {
    //console.log('_do_createRelation', ctx);

    ctx.name = ctx.name?.trim();

    if (!ctx.name) {
      throw new Error('Empty relation name');
    }

    let post_data = Object.assign({}, ctx);
    delete post_data.pending_edge;

    const rawResponse = await fetch('/rest/entity_relation/', {
      method: 'POST',
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

    this.g.relations[content['id']] = content;
    let newEdge = this._toEdge(content['id']);
    this.cy.add(newEdge);
  }
  _renameRelation(renamedEdge) {
    //console.log('_renameRelation', renamedEdge);
    let ctx = {
      name: renamedEdge.data('name'),
      pending_edge: renamedEdge,
    };
    let view = entity_relation_view(ctx, this.allStyles);
    view.find('button[role=save]').click(() => {
      ctx.name = view.find('input[name="name"]').val();
      this._do_renameRelation(ctx)
        .then(this._cancelRelation.bind(this, ctx, false))
        .catch(this._cancelRelation.bind(this, ctx, false));
    });
    view.find('button[role=cancel]').click(this._cancelRelation.bind(this, ctx, false));
    this.sidePaneContent( view );
    view.find('input[name="name"]').select();
  }
  async _do_renameRelation(ctx) {
    //console.log('_do_renameRelation', ctx);
    ctx.name = ctx.name?.trim();
    if (!ctx.name) {
      throw new Error('Empty relation name');
    }

    let post_data = Object.assign({}, ctx);
    delete post_data.pending_edge;

    const rawResponse = await fetch(`/rest/entity_relation/${ctx.pending_edge.id()}/`, {
      method: 'PATCH',
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

    ctx.pending_edge.data('name', ctx.name);
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
  }
  _quickEditEntity(node) {
    let ctx = {
      edited_node: node,
      id: node.id(),
      type: node.data('type'),
      name: node.data('name'),
      super_type: node.data('super_type'),
      content: node.data('content'),
    };
    this._createOrEditEntity(ctx);
  }
  _cancelCreation(ctx, error) {
    if (error) {
      console.error('Entity creation canceled', error);
    }
    this.sidepane(false);
  }
  async _validate_createOrEditEntity(ctx) {
    ctx.name = ctx.name.trim();
    if (!ctx.name) throw new Error("Entity name can't be empty");
    //if (!ctx.type) throw new Error("Entity type must be selected");
    return ctx;
  }
  async _do_createOrEditEntity(ctx) {
    console.log('_do_createOrEditEntity', ctx);

    let post_data = Object.assign({}, ctx);
    delete post_data.position;
    if (post_data.edited_node)
      delete post_data.edited_node;

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
      ctx.edited_node.data('name', content.name);
      ctx.edited_node.data('content', content.content);
      ctx.edited_node.data('type', content.type);
    }
    else {
      // Create
      let newNode = this._toNode(content['id']);
      this.cy.add(newNode).position(ctx.position);
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
    let view = details_view(content, this.allStyles);
    view.find('button[role=close]').click(() => {
      this.sidepane(false);
    });
    view.find('button[role=edit]').click(() => {
      this._quickEditEntity(node);
      //this.sidepane(false);
    });
    this.sidePaneContent( view );
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
      this.cy.on('dbltap', (e) => {
        let node = e.target;
        //console.log('dbltap', e.position);
        if (e.target === this.cy || e.target.isEdge()) {
          this.sidepane(false);
        } else {
          this._viewDetail(node)
              .then(console.log)
              .catch(console.error);
        }
      });
    }

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
        //this.refreshGraph();
      });
      this.jOverlayMenu.append(this.jOverlayMenu_Recenter);
    }
    // Snapshot
    if (this._config.snapshot && !this.jOverlayMenu_Snapshot) {
      this.jOverlayMenu_Snapshot = overlay_button('fa-camera', 'Snapshot');
      this.jOverlayMenu_Snapshot.click((e)=> {
        e.stopPropagation();
        e.preventDefault();
        let png64 = this.cy.png({full:true});
        console.log(png64);
        let image = new Image();
        image.src = png64;
        let w = window.open("");
        w.document.write(image.outerHTML);
      });
      this.jOverlayMenu.append(this.jOverlayMenu_Snapshot);
    }
    // Sidebar toggle
    if (this._config.sidepane && !this.jOverlayMenu_Sidepane) {
      //this.jOverlayMenu_Sidepane = $(`<div class='sidepane'><iframe/></div>`);
      this.jOverlayMenu_Sidepane = $(`<div class='sidepane'></div>`);
      this.jRootElement.append(this.jOverlayMenu_Sidepane);
      //this.jSidepane_IFrame = this.jOverlayMenu_Sidepane.find('iframe');
      //this.jOverlayMenu_SidepaneButton = overlay_button('fa-window-maximize', 'Side pane');
      // this.jOverlayMenu_SidepaneButton.click((e)=> {
      //   e.stopPropagation();
      //   e.preventDefault();
      //   this.jRootElement.toggleClass('sidepane-active');
      // });
      this.sidepane = (t) => {
        this.jRootElement.toggleClass('sidepane-active', t);
      };
      this.sidePaneContent = (c) => {
        this.jOverlayMenu_Sidepane.empty().append(c);
        this.sidepane(true);
      };
      // this.jOverlayMenu.append(this.jOverlayMenu_SidepaneButton);
    }
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
  refreshGraph() {
    /*
    let ly = this.cy.layout( {
      nodeDimensionsIncludeLabels: true,
      name: 'elk',
      elk: {
        // All options are available at http://www.eclipse.org/elk/reference.html
        //
        // 'org.eclipse.' can be dropped from the identifier. The subsequent identifier has to be used as property key in quotes.
        // E.g. for 'org.eclipse.elk.direction' use:
        // 'elk.direction'
        //
        // Enums use the name of the enum as string e.g. instead of Direction.DOWN use:
        // 'elk.direction': 'DOWN'
        //edgeSpacingFactor: 1,
        //inLayerSpacingFactor: 4,
        //fixedAlignment: 'BALANCED',
        'algorithm': 'layered',
        'elk.direction': 'RIGHT',
        'elk.spacing.nodeNode': 70.,
      }
    } ).run();
    */
    if ( this.firstLayout === undefined ) {
      this.firstLayout = true;
    }
    else {
      this.firstLayout = false;
    }

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