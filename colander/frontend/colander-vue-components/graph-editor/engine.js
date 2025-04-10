import '@ungap/custom-elements';

import cytoscape from 'cytoscape';
import Color from 'color';
import contextMenus from 'cytoscape-context-menus';
import edgehandles from 'cytoscape-edgehandles';
import fcose from 'cytoscape-fcose';
import layoutUtilities from 'cytoscape-layout-utilities';
import {color_scheme, icons} from './refs/default-style';
import {overlay_button} from './refs/graph-templates';
import {nodeBody} from './refs/functional-styles.js';

// For sub-vue access
import MarkdownIt from 'markdown-it';

window.Markdown = new MarkdownIt({breaks:true});

cytoscape.use( contextMenus );
cytoscape.use( edgehandles );
cytoscape.use( layoutUtilities ); // Optional but used by fcose in our case
cytoscape.use( fcose );

let styles = [];

styles.push({
  selector: 'node',
  style: {
    //'background-blacken': -0.5,
    'shape': 'round-rectangle',
    'border-width': 2,
    'font-family': 'sans-serif, ForkAwesome',
    'font-size': '10px',
    'line-height': 1.25,
    'text-halign': 'center',
    'text-valign': 'center',
    'text-wrap': 'wrap',
    'text-outline-color': 'white',
    'text-outline-opacity': 1,
    'text-outline-width': 2,
    'display': (e) => {
      return e.scratch('_overrides')?.hidden ? 'none' : 'element';
    },
  }
});

for(let iid in icons) {
  styles.push({
    selector: `node.${iid}`,
    style: {
      'background-color': Color(color_scheme[iid]).mix(Color.rgb(255,255,255), 0.5).hsl().string(),
      'border-color': color_scheme[iid],
      'text-outline-color': Color(color_scheme[iid]).mix(Color.rgb(255,255,255), 0.5).hsl().string(),
      'label': (e)=> { return nodeBody(e, iid).svgTxt; },
      'text-halign': (e)=> { return nodeBody(e, iid).labelHAlign; },
      'text-justification': (e)=> { return nodeBody(e, iid).labelJustification; },
      'width': (e) => { return nodeBody(e, iid).width; },
      'height': (e) => { return nodeBody(e, iid).height; },
      'background-image': (e) => { return nodeBody(e, iid).bgImage; },
      'background-clip': 'node',
      'background-fit': 'contain',
      'text-margin-x': (e) => { return nodeBody(e, iid).labelMarginX; },
      'background-position-x': '0px', // if on the left
    }
  });
}

styles.push({
  selector: `node[!on-thumbnail]:selected`,
  style: {
    'background-color': '#7122da',
    'border-color': '#7122da',
    'text-outline-color': '#7122da',
    'background-blacken': 0,
    'color': 'white',
  }
});

styles.push({
  selector: `node.highlighted`,
  style: {
    'underlay-color': '#7122da',
    'underlay-padding': '10px',
    'underlay-opacity': 0.5,
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
  }
});

styles.push({
  selector: 'edge:loop',
  style: {
    'curve-style': 'bezier',
    'loop-direction': '0deg',
    'loop-sweep': '-45deg',
  }
});

styles.push({
  selector: `edge:selected`,
  style: {
    'line-color': '#999',
    'target-arrow-color': '#999',
  }
});

styles.push({
  selector: `edge[!on-thumbnail]:selected`,
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
    'label': (ele) => { return `\uf023 ${ele.data('name')}`;}
  }
});

styles.push({
  selector: '.hidden',
  style: {
    'display': 'none',
  }
});

class ColanderDGraph {
  // Attributes
  $vue;
  jRootElement;
  cy;
  g;
  jOverlayMenu;
  _config;

  constructor(vueCtx, config) {
    this.$vue = vueCtx;

    this.config( config || {} );

    this._domSetup();

    fetch('/rest/dataset/all_styles/')
      .then((r) => r.json())
      .then(this._onStyleFetched.bind(this))
      .catch(console.error);
  }

  _domSetup() {
    this.jRootElement = $(this.$vue.$el);
    //this.jRootElement.addClass('colander-dgraph');

    // Encapsulate a sub-container to prevent buttons and sidepane event chaos
    // when childing stuff to cytoscape root element

    this.jGraphElement = this.jRootElement.find('.graph-sub-container');
    /*
    this.jGraphElement = $(`<div class='graph-sub-container'/>`)
    this.jRootElement.append(this.jGraphElement);
    */
    this.jOverlayMenu = this.jRootElement.find('.graph-overlay-menu');
    /*
    this.jOverlayMenu = $(`<div class="graph-overlay-menu position-absolute top-0 start-0" style="z-index: 20;">`);
    this.jRootElement.append(this.jOverlayMenu);
    */

    this.jLoading = this.jRootElement.find('.graph-loading');
    /*
    this.jLoading = $(`<div class="graph-loading">
        <div class="spinner-border" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
    </div>`);
    this.jRootElement.append(this.jLoading);
    */
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

    const pipDimension = { w: 40, h: 40 };
    const pipOffset = { w: 18, h: 0 };

    this._applyInternalConfig();
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


    // Enhance ctxmenu
    // - disable 'selected' entries depending on selection state
    this.cy.on('cxttap', 'node', (e) => {
      let node = e.target;
      let selection = this.cy.$(':selected');
      if (selection.empty()) {
        this.contextMenu.disableMenuItem('subgraph-create');
        if (this._config.editableVisibility)
          this.contextMenu.disableMenuItem('hide-entity-selected');
      }
      else {
        if (!selection.contains(node)) {
          node.select();
        }
        this.contextMenu.enableMenuItem('subgraph-create');
        if (this._config.editableVisibility)
          this.contextMenu.enableMenuItem('hide-entity-selected');
      }
    });


    //
    // -- Context menu (right-click) plugin
    if (!this.contextMenu) {
      let contextMenuItems = [];
      contextMenuItems.push({
        id: 'relation-create',
        content: 'Create relation',
        tooltipText: 'Add relation between two entities',
        selector: 'node',
        image: {src: '/static/images/icons/link.svg', width: 12, height: 12, x: 4, y: 7},
        onClickFunction: (e) => {
          let node = e.target;
          this.edgeHandler.start(node);
        }
      });
      contextMenuItems.push({
        id: 'relation-rename',
        content: 'Rename relation',
        tooltipText: 'Add relation between two entities',
        selector: 'edge.mutable',
        image: {src: '/static/images/icons/pencil-square-o.svg', width: 12, height: 12, x: 4, y: 7},
        onClickFunction: (e) => {
          let edge = e.target;
          this._renameRelation(edge);
        }
      });
      contextMenuItems.push({
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
      });
      contextMenuItems.push({
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
      });
      contextMenuItems.push({
        id: 'entity-edit',
        content: 'Quick edit entity',
        tooltipText: 'Quick edit',
        selector: 'node',
        image: {src: '/static/images/icons/pencil-square-o.svg', width: 12, height: 12, x: 4, y: 7},
        onClickFunction: (e) => {
          let node = e.target;
          this._quickEditEntity(node);
        }
      });
      if (this._config.editableVisibility) {
        contextMenuItems.push({
          id: 'hide-entity',
          content: 'Hide entity',
          tooltipText: 'Hide selected entities',
          selector: 'node',
          image: {src: '/static/images/icons/eye-slash.svg', width: 12, height: 12, x: 4, y: 7},
          onClickFunction: (e) => {
            this._hideEntities(e.target, 0);
          },
          submenu: [
            {
              id: 'hide-entity-selected',
              content: 'Selected',
              tooltipText: 'Hide selected entities',
              selector: 'node',
              image: {src: '/static/images/icons/eye-slash.svg', width: 12, height: 12, x: 4, y: 7},
              onClickFunction: (e) => {
                let selection = this.cy.$(':selected');
                this._hideEntities(selection, 0);
              },
            },
            {
              id: 'hide-entity-1',
              content: '+1 degree',
              tooltipText: 'Hide entity and 1 degree neighbors',
              selector: 'node',
              image: {src: '/static/images/icons/eye-slash.svg', width: 12, height: 12, x: 4, y: 7},
              onClickFunction: (e) => {
                this._hideEntities(e.target, 1);
              },
            },
            {
              id: 'hide-entity-2',
              content: '+2 degree',
              tooltipText: 'Hide entity and 2 degrees neighbors',
              selector: 'node',
              image: {src: '/static/images/icons/eye-slash.svg', width: 12, height: 12, x: 4, y: 7},
              onClickFunction: (e) => {
                this._hideEntities(e.target, 2);
              },
            },
            {
              id: 'hide-entity-all',
              content: 'All linked',
              tooltipText: 'Hide entity and all neighbors tree',
              selector: 'node',
              image: {src: '/static/images/icons/eye-slash.svg', width: 12, height: 12, x: 4, y: 7},
              onClickFunction: (e) => {
                this._hideEntities(e.target);
              },
            },
          ]
        });
        contextMenuItems.push({
          id: 'show-entity',
          content: 'Show entity',
          tooltipText: 'Show all linked entities',
          selector: 'node',
          image: {src: '/static/images/icons/eye.svg', width: 12, height: 12, x: 4, y: 7},
          onClickFunction: (e) => {
            let node = e.target;
            let linked = ColanderDGraph.cy_linked(node);
            linked.filter('node').forEach((ele) => {
              if (ele.id() === node.id()) return;
              this.g.overrides[ele.id()] = this.g.overrides[ele.id()] || {};
              this.g.overrides[ele.id()].hidden = false;
              delete this.fixedPosition[ele.id()];
            });
            linked.select().unselect();
            //linked.select();
            this.refreshGraph();
          },
          submenu: [
            {
              id: 'show-entity-1',
              content: '+1 degree',
              tooltipText: 'Show 1 degree neighbors entities',
              selector: 'node',
              image: {src: '/static/images/icons/eye.svg', width: 12, height: 12, x: 4, y: 7},
              onClickFunction: (e) => {
                this._showEntitiesAndRelax(e.target, 1);
              },
            },
            {
              id: 'show-entity-2',
              content: '+2 degree',
              tooltipText: 'Show 2 degree neighbors entities',
              selector: 'node',
              image: {src: '/static/images/icons/eye.svg', width: 12, height: 12, x: 4, y: 7},
              onClickFunction: (e) => {
                this._showEntitiesAndRelax(e.target, 2);
              },
            },
            {
              id: 'show-entity-all',
              content: 'All linked',
              tooltipText: 'Show all tree neighbors entities',
              selector: 'node',
              image: {src: '/static/images/icons/eye.svg', width: 12, height: 12, x: 4, y: 7},
              onClickFunction: (e) => {
                this._showEntitiesAndRelax(e.target);
              },
            },
          ],
        });
      }
      contextMenuItems.push({
        id: 'select-entity',
        content: 'Select entity',
        tooltipText: 'Select entity',
        selector: 'node,edge',
        image: {src: '/static/images/icons/selection-add.svg', width: 12, height: 12, x: 4, y: 7},
        onClickFunction: (e) => {
          //let linked = ColanderDGraph.cy_linked(e.target);
          //linked.select();
          e.target.select();
        },
        submenu: [
          {
            id: 'select-entity-1',
            content: '+1 degree',
            tooltipText: 'Select entity and 1 degree neighbors',
            selector: 'node,edge',
            image: {src: '/static/images/icons/selection-add.svg', width: 12, height: 12, x: 4, y: 7},
            onClickFunction: (e) => {
              let linked = ColanderDGraph.cy_linked(e.target, 1);
              linked.select();
            },
          },
          {
            id: 'select-entity-2',
            content: '+2 degree',
            tooltipText: 'Select entity and 2 degree neighbors',
            selector: 'node,edge',
            image: {src: '/static/images/icons/selection-add.svg', width: 12, height: 12, x: 4, y: 7},
            onClickFunction: (e) => {
              let linked = ColanderDGraph.cy_linked(e.target, 2);
              linked.select();
            },
          },
          {
            id: 'select-entity-all',
            content: 'All tree',
            tooltipText: 'Select entity and all neighbors tree',
            selector: 'node,edge',
            image: {src: '/static/images/icons/selection-add.svg', width: 12, height: 12, x: 4, y: 7},
            onClickFunction: (e) => {
              let linked = ColanderDGraph.cy_linked(e.target);
              linked.select();
            },
          },
        ],
      });
      contextMenuItems.push({
        id: 'relax-linked',
        content: 'Relax linked',
        tooltipText: 'Relax all linked entities',
        selector: 'node',
        image: {src: '/static/images/icons/magic.svg', width: 12, height: 12, x: 4, y: 7},
        onClickFunction: (e) => {
          let linked = ColanderDGraph.cy_linked(e.target);

          for(let ele of linked) {
            delete this.fixedPosition[ele.id()];
          }

          this.refreshGraph();
        }
      });
      contextMenuItems.push({
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
      });
      contextMenuItems.push({
        id: 'subgraph-create',
        content: 'Create sub-graph',
        tooltipText: 'Create sub-graph of selected entities',
        selector: 'node',
        image: {src: '/static/images/icons/hubzilla.svg', width: 12, height: 12, x: 4, y: 7},
        onClickFunction: (e) => {
          let selection = this.cy.$('node:selected');
          this._createSubGraph(selection);
        }
      });
      if (this._config.sendToDocumentation) {
        contextMenuItems.push({
          id: 'add-linked-to-doc',
          content: 'Add to documentation',
          tooltipText: 'Add linked tree to documentation',
          selector: 'node',
          image: {src: '/static/images/icons/hubzilla.svg', width: 12, height: 12, x: 4, y: 7},
          onClickFunction: (e) => {
            let linked = ColanderDGraph.cy_linked(e.target);
            console.log('linked', linked);
            let complement = linked.absoluteComplement();
            complement.addClass('hidden');
            let png64 = this.cy.png({full: true, bg: 'white', scale: 2});

            complement.removeClass('hidden');

            this.$bus.emit('documentation-add-image', `![Sub Graph](${png64})`);
          }
        });
      }

      this.contextMenu = this.cy.contextMenus({
        menuItems: contextMenuItems,
        submenuIndicator: {src: '/static/images/icons/caret-right.svg', width: 12, height: 12, x: 4, y: 4},
      });
    } /* end on contextMenu */

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
      //this.jOverlayMenu_Sidepane = $(`<div class='sidepane'></div>`);
      //this.jRootElement.append(this.jOverlayMenu_Sidepane);
      this.jOverlayMenu_Sidepane = this.jRootElement.find('.sidepane');
      this.$vue.$debug('jOverlayMenu_Sidepane', this.jOverlayMenu_Sidepane);


      //
      // Resize stuff sidepane
      let resizing = false;
      let previous_screen_x = 0;
      this.sidepane_width = this.jOverlayMenu_Sidepane.outerWidth();
      this.jRootElement.mousedown((e) => {
        resizing = e.offsetX < 5;
        if (resizing) {
          this.sidepane_width = this.jOverlayMenu_Sidepane.outerWidth();
          previous_screen_x = e.screenX;
          e.preventDefault();
          e.stopPropagation();
        }
      }).mousemove((e) => {
        if (!resizing) return;
        let delta = previous_screen_x - e.screenX;
        previous_screen_x = e.screenX;
        this.sidepane_width = Math.max(40, (this.sidepane_width + delta));
        this.jOverlayMenu_Sidepane.get(0).style.setProperty('--sidepane-width', `${this.sidepane_width}px`);
      }).mouseup((e) => {
        resizing = false;
      }).mouseleave((e) => {
        resizing = false;
      });
      // End: Resize stuff sidepane
      //

      this.sidepane = (falseOrPaneRef) => {
        // Current active (if one)
        if (typeof(falseOrPaneRef) === 'boolean') {
          //this.jRootElement.toggleClass('sidepane-active', t);
          this.$vue.setSidepane(falseOrPaneRef);
        }
        if (typeof(falseOrPaneRef) === 'object') {
          //this.jOverlayMenu_Sidepane.find('.vue-component').removeClass('active');
          //t.addClass('active');
          //this.jRootElement.toggleClass('sidepane-active', true);
          this.$vue.setSidepane(falseOrPaneRef);
        }
      };
      this.sidepane_add = (paneRef) => {
        this.jOverlayMenu_Sidepane.append(pane);
      };
      // this.jOverlayMenu.append(this.jOverlayMenu_SidepaneButton);
    }

    setTimeout( this._init_vues.bind(this) );
  }

  _init_vues() {
    //
    // Entities list
    // ========================================================================
    this._sidepane_entities_overview = this.$vue.$refs.entityTablePane;
    $(this._sidepane_entities_overview.$el).on('close-component', (e) => {
      this.$vue.$debug('on close-component');
      this.sidepane(false);
    });

    this.$vue.$debug('on vue-ready');
    this.$vue.$refs.entityTablePane.editableVisibility = this._config.editableVisibility || false;
    this.$vue.$refs.entityTablePane.allStyles = this.allStyles;
    if (this.g) {
      // Carefull: this.g (aka graph data) comes very late
      // Usually this.g is not available at this state.
      // @see _onGraphData() to handle this
      this.$vue.$refs.entityTablePane.overrides = this.g.overrides;
      this.$vue.$refs.entityTablePane.entities = this.g.entities;
    }

    $(this._sidepane_entities_overview.$el).on('entity-visibility-changed', (e, eid, hidden) => {
      let node = this.cy.$id(eid);
      // Hack:
      // 'selecting' then 'unselecting' node
      // force node:style:display:cb() to be recomputed
      // Without that, the callback is never triggered after hiding a node.
      // ... then we emit a 'free' event
      node.select().unselect();
      if (hidden) {
        node.emit('free');
      }
      else {
        $(this._sidepane_entities_overview.$el).trigger('focus-entity', [eid]);
        if (this._config.layoutAfterNodeBecomeVisible) {
          setTimeout(() => {
            delete this.fixedPosition[eid];
            // refreshGraph will emit 'free' like events
            this.refreshGraph();
          }, 1500);
        }
      }
    });
    $(this._sidepane_entities_overview.$el).on('focus-entity', (e, eid) => {
      let pos = this.cy.$id(eid).renderedPosition();
      let pan = this.cy.pan();
      let viewport = { x: this.cy.width(), y:this.cy.height() };

      this.cy.$id(eid).flashClass('highlighted', 2000);

      this.cy.animate({
        //center: { eles: this.cy.$id(eid) },
        //zoom: 2,
        pan: { x:pan.x-pos.x+(viewport.x-this.sidepane_width)/2, y:pan.y-pos.y+viewport.y/2 },
        easing: 'ease-in-out',
        duration: 1500,
      });
    });

    //
    // Entity edit form
    // ========================================================================
    this._sidepane_entity_create_or_edit = this.$vue.$refs.entityEditPane;

    this.$vue.$refs.entityEditPane.allStyles = this.allStyles;

    $(this._sidepane_entity_create_or_edit.$el).on('close-component', (e) => {
      this.sidepane(false);
    });
    $(this._sidepane_entity_create_or_edit.$el).on('save-entity', (e, entity) => {
      this._do_createOrEditEntity(entity)
        .then(console.log).catch(console.error);
      this.sidepane(false);
    });

    return;

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
      this._sidepane_entity_create_or_edit.edit_entity( tmp );
      this.sidepane(  this._sidepane_entity_create_or_edit );
    });

    //
    // SubGraph creation/edit form
    // ========================================================================
    this._sidepane_subgraph_create_or_edit = vueComponent('colander-dgraph-subgraph-form');
    this.sidepane_add(this._sidepane_subgraph_create_or_edit);
    this._sidepane_subgraph_create_or_edit.on('vue-ready',(e,jDom,vue) => {
      vue.allStyles = this.allStyles;
    });
    this._sidepane_subgraph_create_or_edit.on('close-component', (e) => {
      this.sidepane(false);
    });
    this._sidepane_subgraph_create_or_edit.on('save-subgraph', (e, subgraph, editNow) => {
      console.log('save-subgraph', subgraph);
      this._do_createOrEditSubGraph(subgraph)
        .then((subgraphObj) => {
          if (editNow && subgraphObj.absolute_url) {
            window.location.assign(subgraphObj.absolute_url);
          }
        }).catch(console.error);
      this.sidepane(false);
    });

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

    // 1- Gather entities positions
    for(let nid in this.fixedPosition) {
      post_data[nid] = {
        position: this.fixedPosition[nid].position,
      };
      if (this._config.editableVisibility) {
        post_data[nid].hidden = (this.g.overrides[nid] && this.g.overrides[nid].hidden) || false;
      }
    }

    // 2- Generate thumbnail
    if (this._config.generateThumbnail) {

      this.cy.$(':selected').data('on-thumbnail', true);

      let thumbnailBlob = this.cy.png({
        output: 'blob',
        full: true,
        bg: 'white',
        maxWidth: 256,
        maxHeight: 144
      });

      this.cy.$(':selected').data('on-thumbnail', false);

      let offscreenCanvas = document.createElement('canvas');
      let ctx2D = offscreenCanvas.getContext("2d");
      offscreenCanvas.width = 256;
      offscreenCanvas.height = 144;
      ctx2D.rect(0, 0, offscreenCanvas.width, offscreenCanvas.height);
      ctx2D.fillStyle = 'white';
      ctx2D.fill();

      if (thumbnailBlob.size > 0) {
        let thumbnailImg = await createImageBitmap(thumbnailBlob);
        ctx2D.drawImage(
          thumbnailImg,
          (offscreenCanvas.width - thumbnailImg.width) / 2,
          (offscreenCanvas.height - thumbnailImg.height) / 2
        );
        thumbnailImg = null;
      }
      post_data['thumbnail'] = offscreenCanvas.toDataURL().replace(/^.+,/, '');

      ctx2D = null;
      offscreenCanvas = null;
      thumbnailBlob = null;
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

    // Ensure we have defaults
    let overridesAtFirst = true;
    if (!this.g.overrides) {
      this.g.overrides = {};
      overridesAtFirst = false;
    }

    for(let eid in this.g.entities) {
      let n = this._toNode(eid);
      let node = this.cy.add(n);
      this.g.overrides[node.id()] = this.g.overrides[node.id()] || {
        // depending if graph or subgraph
        // newly created 'entities' (outside this subgraph)
        // are hidden by default
        // unless if a subgraph have never been opened/intialized
        hidden: this._config.editableVisibility && overridesAtFirst,
      };
    }
    for(let rid in this.g.relations) {
      let e = this._toEdge(rid);
      this.cy.add(e);
    }

    // This part is strongly dependent to the layout engine used
    // In our case (for now), it's fcose
    for(let nid in this.g.overrides) {
      // Check if an override is still in current entities ecosystem.
      // If not, cytoscape override system does not support unknown 'override'
      // "delete"s any override no more relevant (by omitting it in referenced fixedPotitions).
      if (nid in this.g.entities === false) continue;

      this.cy.$id(nid).scratch('_overrides', this.g.overrides[nid]);

      if (this.g.overrides[nid].position) {
        this.fixedPosition[nid] = {
          nodeId: nid,
          position: this.g.overrides[nid].position,
        }
      }
    }

    if (this._sidepane_entities_overview) {
      //let vue = this._sidepane_entities_overview.data('vue');
      let vue = this._sidepane_entities_overview;
      // Workaround a race condition between graph data coming and sub-vue-component inited.
      if (vue) {
        // graph data comes late
        vue.overrides = this.g.overrides;
        vue.entities = this.g.entities;
      }
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

    let post_data = Object.assign({
      case_id: this._config.caseId
    }, ctx);
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
      name: null,
      position: position,
    };
    this._createOrEditEntity(ctx);
  }

  _createOrEditEntity(ctx) {
    this._sidepane_entity_create_or_edit.edit_entity(ctx);
    this.sidepane(  this._sidepane_entity_create_or_edit );
  }

  _quickEditEntity(node) {
    this.$vue.$debug('_quickEditEntity node:', node);
    let ctx = {
      //edited_node: node, // due to internal structure of a cy node,
                           // passing this kind of value to vue makes vue
                           // hangs forever in instrumenting 'edited_node' attribute
      id: node.id(),
      type: node.data('type'),
      name: node.data('name'),
      super_type: node.data('super_type'),
      content: node.data('content'),
      thumbnail_url: node.data('thumbnail_url'),
    };
    this._createOrEditEntity(ctx);
  }

  async _do_createOrEditEntity(ctx) {
    let post_data = Object.assign({
      case_id: this._config.caseId
    }, ctx);
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
      let nodeElem = this.cy.add(newNode);
      nodeElem.position(ctx.position).emit('free');
      this.g.overrides[nodeElem.id()] = { hidden: false };
      nodeElem.scratch('_overrides', this.g.overrides[nodeElem.id()]);

      if (this._sidepane_entities_overview) {
        this._sidepane_entities_overview.track_new_entity(content);
      }
    }

    if (this._sidepane_entities_overview) {
      this._sidepane_entities_overview.refresh();
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

  _createSubGraph(selection) {
    let overrides = {};
    selection.forEach((ele) => {
      overrides[ele.id()] = {
        hidden: false,
      };
    });
    let ctx = {
      overrides: overrides,
    };
    this._createOrEditSubGraph(ctx);
  }

  _createOrEditSubGraph(ctx) {
    this._sidepane_subgraph_create_or_edit.data('vue').entities = this.g.entities;
    this._sidepane_subgraph_create_or_edit.data('vue').subgraph = ctx;
    this.sidepane(this._sidepane_subgraph_create_or_edit);
  }

  async _do_createOrEditSubGraph(ctx) {
    let post_data = Object.assign({
      case: this._config.caseId
    }, ctx);

    const rawResponse = await fetch(
        ctx.id?`/rest/subgraph/${ctx.id}/`:'/rest/subgraph/',
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
    return content;
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

  _hideEntities(eles, degree) {
    if (degree === undefined) {
      degree = Number.MAX_SAFE_INTEGER;
    }
    if (degree > 0) {
      eles = ColanderDGraph.cy_linked(eles, degree);
    }
    eles.filter('node').forEach((ele) => {
      this.g.overrides[ele.id()] = this.g.overrides[ele.id()] || {};
      this.g.overrides[ele.id()].hidden = true;
    });
    eles.select().unselect().emit('free');
    this._sidepane_entities_overview?.refresh();
  }

  _showEntitiesAndRelax(orignalEles, degree) {
    if (degree === undefined) {
      degree = Number.MAX_SAFE_INTEGER;
    }
    let eles = orignalEles;
    if (degree > 0) {
      eles = ColanderDGraph.cy_linked(orignalEles, degree);
    }
    eles.filter('node').forEach((ele) => {
      if (orignalEles.contains(ele)) return;
      this.g.overrides[ele.id()] = this.g.overrides[ele.id()] || {};
      this.g.overrides[ele.id()].hidden = false;
      delete this.fixedPosition[ele.id()];
    });
    eles.select().unselect();
    this._sidepane_entities_overview?.refresh();
    this.refreshGraph();
  }

  static cy_linked(ele, degree) {
    degree = degree || Number.MAX_SAFE_INTEGER;
    let selection = ele;
    if (selection.isEdge()) {
      selection = selection.connectedNodes()
    }
    let currentCount = selection.length;
    do {
      currentCount = selection.length
      selection = selection.closedNeighborhood();
    } while( currentCount < selection.length && --degree > 0);
    return selection;
  }

  refreshGraph() {

    this.firstLayout = this.firstLayout === undefined;

    let ly = this.cy.layout({
      name: 'fcose',
      quality: 'proof',
      randomize: this.firstLayout,
      fit: this.firstLayout,
      animate: !this.firstLayout,
      animationDuration: 500,
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

export default ColanderDGraph;
