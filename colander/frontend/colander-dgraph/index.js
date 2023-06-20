import cytoscape from 'cytoscape';
import _ from 'lodash';
import contextMenus from 'cytoscape-context-menus';
import edgehandles from 'cytoscape-edgehandles';
//import klay from 'cytoscape-klay';
import elk from 'cytoscape-elk';
import {icons, icon_unicodes, color_scheme, shapes, base_styles} from './default-style';

cytoscape.use( contextMenus );
cytoscape.use( edgehandles );
cytoscape.use( elk );
//cytoscape.use( klay );

console.log('memoize', _.memoize);

let styles = [];

for(let iid in icons) {
  styles.push({
    selector: `node.${iid}`,
    style: {
      'background-color': color_scheme[iid],
      'background-blacken': -0.5,
      'shape': shapes[iid],
      'border-color': color_scheme[iid],
      'border-width': 3,
      'label': (e) => {
        return `${icon_unicodes[iid]}    ${e.data('name')}\n${e.data('type')||''}`;
      },
      /*
      'label': (e) => {
        return `<span class="fa ${icons[iid]} fa-2x"></span> ${e.data('name')}`;
      },
      */
      'font-family': 'ForkAwesome, sans-serif',
      'letter-spacing': '15px',
      'font-size': '10px',
      //'width': 'label',
      'width': (e) => { return e.data('name').length * 6 + 40; },
      'text-halign': 'center',
      'text-valign': 'center',
      'text-wrap': 'wrap',
    }
  });
}
styles.push({
  selector: `node:selected`,
  style: {
    'background-color': '#7122da',
    'border-color': '#7122da',
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
    'font-family': 'ForkAwesome, sans-serif',
    'letter-spacing': '15px',
    'font-size': '10px',
    'curve-style': 'bezier',
    'loop-direction': '0deg',
    'loop-sweep': '-45deg',
    //'line-style': 'dashed',
  }
});

styles.push({
  selector: 'edge.eh-ghost-edge',
  style: {
    'label': '',
  }
});


styles.push({
  selector: 'edge.immutable',
  style: {
    //'color': 'purple',
    'label': (ele) => { return '\uf023'+'    '+ele.data('name');}
    //'text-outline-color': 'red',
  }
});

async function create_relation(csrf, source, target, name) {
  const rawResponse = await fetch('/rest/entity_relations/', {
    method: 'POST',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
      'X-CSRFToken': csrf,
    },
    body: JSON.stringify({
      name: name,
      obj_from: source,
      obj_to: target,
    })
  })
  const content = await rawResponse.json();

  console.log('create_relation', content);
}

class ColanderDGraph {
  // Attributes
  jRootElement;
  graphUrl;
  cy;
  g;
  jOverlayMenu;
  options;
  csrf;
  constructor(idElement, graphUrl, csrf) {
    this.csrf = csrf;
    this.jRootElement = $(`#${idElement}`);
    this.jRootElement.addClass('colander-dgraph');
    this.graphUrl = graphUrl;
    this.cy = cytoscape({
      container: $('#ze-graph'),
      userZoomingEnabled: true,
      userPanningEnabled: true,
      boxSelectionEnabled: true,
      wheelSensitivity: 0.5,
      style: styles,
      ready: this._onCyReady.bind(this)
    });
    //
    // -- Edge (creation) handling plugin
    let eh = this.cy.edgehandles({
      canConnect: function( sourceNode, targetNode ){
        //return !sourceNode.same(targetNode); // disallow loops
        return true; // allow loops
      },
      edgeParams: (sourceNode, targetNode) => {
        // Temporary set the new edge name
        // will be overridden by user with edge name prompt
        return { data: {name: 'New relation'} };
      },
      snap: false,
    });
    this.cy.on('ehcomplete', this._createRelation.bind(this));

    let menu = this.cy.contextMenus({
      menuItems: [
        {
          id: 'relation-create',
          content: 'Create Relation',
          tooltipText: 'Add relation between two entities',
          selector: 'node',
          image: { src:'/static/images/icons/link.svg', width: 12, height: 12, x: 4, y:7 },
          onClickFunction: (e) => {
            let node = e.target;
            console.log('create-relation', node)
            eh.start(node);
          }
        },
        {
          id: 'relation-rename',
          content: 'Rename relation',
          tooltipText: 'Add relation between two entities',
          selector: 'edge.mutable',
          image: { src:'/static/images/icons/pencil-square-o.svg', width: 12, height: 12, x: 4, y:7 },
          onClickFunction: (e) => {
            let edge = e.target;
            console.log('relation-rename', edge)
            this._renameRelation(edge)
                .then(console.log)
                .catch(console.error);
          }
        },
        {
          id: 'relation-delete',
          content: 'Delete relation',
          tooltipText: 'Delete relation between two entities',
          selector: 'edge.mutable',
          image: { src:'/static/images/icons/trash.svg', width: 12, height: 12, x: 4, y:7 },
          onClickFunction: (e) => {
            let edge = e.target;
            console.log('delete-relation', edge)
            this._deleteRelation(edge)
                .then(console.log)
                .catch(console.error);
          }
        },
        {
          id: 'entity-details',
          content: 'View entity details',
          tooltipText: 'View entity details',
          selector: 'node',
          image: { src:'/static/images/icons/eye.svg', width: 12, height: 12, x: 4, y:7 },
          onClickFunction: (e) => {
            let node = e.target;
            console.log('create-relation', node);
            window.location = node.data('absolute_url');
            //eh.start(node);
          }
        },
        {
          id: 'entity-edit',
          content: 'Edit entity',
          tooltipText: 'Edit entity details',
          selector: 'node',
          image: { src:'/static/images/icons/pencil-square-o.svg', width: 12, height: 12, x: 4, y:7 },
          onClickFunction: (e) => {
            let node = e.target;
            console.log('create-relation', node);
            window.location = node.data('absolute_url');
            //eh.start(node);
          }
        },

        // {
        //   id: 'entity-create',
        //   content: 'Add entity',
        //   tooltipText: 'Create a new entity',
        //   image: { src:'/static/images/icons/plus-circle.svg', width: 12, height: 12, x: 4, y:7 },
        //   //selector: 'node',
        //   coreAsWell: true,
        //   /*
        //   onClickFunction: function () {
        //     console.log('add node');
        //   },
        //
        //    */
        //   submenu: [
        //     {
        //       id: 'create-relation-2',
        //       content: 'Create Relation',
        //       tooltipText: 'Add relation between two entities',
        //       selector: 'node',
        //       image: { src:'/static/images/icons/link.svg', width: 12, height: 12, x: 4, y:7 },
        //       onClickFunction: (e) => {
        //         let node = e.target;
        //         console.log('create-relation', node)
        //         eh.start(node);
        //       }
        //     },
        //   ]
        // }
      ],

      submenuIndicator: { src:'/static/images/icons/caret-right.svg', width: 12, height: 12, x: 4, y:4 },
    });


    console.log('ColanderDGraph prod', idElement, graphUrl, this.jRootElement, this.graphUrl);
  }
  _onCyReady() {
    console.log('Fetching ...');
    fetch(this.graphUrl)
      .then((r) => r.json())
      .then(this._onGraphData.bind(this))
      .catch((e) => {
        console.log('Fetch error', e);
      })
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

    this.refreshGraph();

  }
  async _createRelation(event, sourceNode, targetNode, addedEdge) {
    console.log('_createRelation', addedEdge.data('source'), addedEdge.data('name'), addedEdge.data('target'));
    let rname = window.prompt('Relation name:', addedEdge.data('name'));
    if (rname === null) {
      this.cy.remove(addedEdge);
      // User may have canceled
      return;
    }
    rname = rname.trim();
    if (!rname) {
      this.cy.remove(addedEdge);
      // Empty relation name
      return;
    }

    addedEdge.data('name', rname);

    const rawResponse = await fetch('/rest/entity_relations/', {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-CSRFToken': this.csrf,
      },
      body: JSON.stringify({
        name: addedEdge.data('name'),
        obj_from: sourceNode.id(),
        obj_to: targetNode.id(),
      })
    });

    console.log(rawResponse);
    if (!rawResponse.ok) {
      this.cy.remove(addedEdge);
      alert('Unexcpeted server error');
      return;
    }

    const content = await rawResponse.json();
    console.log('create_relation', content);

    this.cy.remove(addedEdge);
    this.g.relations[content['id']] = content;
    let newEdge = this._toEdge(content['id']);
    this.cy.add(newEdge);
  }
  async _renameRelation(edge) {
    let rname = window.prompt('Relation name:', edge.data('name'));
    if (rname === null) {
      // User canceled
      // Lease it unmodified
      return;
    }
    rname = rname.trim();
    if (!rname) {
      // Empty string
      // Cancel and leave unchanged
      //FIXME: May be do something else
      //eg: remove it
      return;
    }

    const rawResponse = await fetch(`/rest/entity_relations/${edge.id()}/`, {
      method: 'PATCH',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-CSRFToken': this.csrf,
      },
      body: JSON.stringify({
        name: edge.data('name'),
      })
    });

    console.log(rawResponse);
    if (!rawResponse.ok) {
      alert('Unexcpeted server error');
      return;
    }

    edge.data('name', rname);
  }

  async _deleteRelation(edge) {
    const rawResponse = await fetch(`/rest/entity_relations/${edge.id()}/`, {
      method: 'DELETE',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-CSRFToken': this.csrf,
      },
      body: JSON.stringify({})
    });

    console.log(rawResponse);
    if (!rawResponse.ok) {
      alert('Unexcpeted server error');
      return;
    }

    this.cy.remove(edge);
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
  enable(options) {
    this.options = Object.assign(this.options||{}, options);
    if (options.lock)
    {
      this.cy.userZoomingEnabled(!options.lock);
      this.cy.userPanningEnabled(!options.lock);
      this.cy.boxSelectionEnabled(!options.lock);
    }
    if (!this.jOverlayMenu) {
      this.jOverlayMenu = $(`<div class="graph-overlay-menu position-absolute top-0 start-0" style="z-index: 20;">`);
      this.jRootElement.append(this.jOverlayMenu);
    }
    // Full screen editor
    if (options.fullscreen && !this.jOverlayMenu_Fullscreen) {
      this.jOverlayMenu_Fullscreen = $(`<button class="btn btn-sm btn-outline-secondary bg-light" title="Fullscreen">
        <i class="fa fa-arrows-alt" aria-hidden="true"></i>
        <span class="label">Fullscreen</span>
      </button>`);
      this.jOverlayMenu_Fullscreen.click((e)=> {
        e.stopPropagation();
        e.preventDefault();
        this.jRootElement.toggleClass('fullscreen');
      });
      this.jOverlayMenu.append(this.jOverlayMenu_Fullscreen);
    }
    // ReCenter and Fit graph
    if (options.recenter && !this.jOverlayMenu_Recenter) {
      this.jOverlayMenu_Recenter = $(`<button class="btn btn-sm btn-outline-secondary bg-light" title="Re-Center">
        <i class="fa fa-crosshairs" aria-hidden="true"></i>
        <span class="label">Re-Center</span>
      </button>`);
      this.jOverlayMenu_Recenter.click((e)=> {
        e.stopPropagation();
        e.preventDefault();
        this.refreshGraph();
      });
      this.jOverlayMenu.append(this.jOverlayMenu_Recenter);
    }
    // Snapshot
    if (options.snapshot && !this.jOverlayMenu_Snapshot) {
      this.jOverlayMenu_Snapshot = $(`<button class="btn btn-sm btn-outline-secondary bg-light" title="Snapshot">
        <i class="fa fa-camera" aria-hidden="true"></i>
        <span class="label">Snapshot</span>
      </button>`);
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
    if (options.sidepane && !this.jOverlayMenu_Sidepane) {
      this.jOverlayMenu_Sidepane = $(`<div class='sidepane'><iframe/></div>`);
      this.jRootElement.append(this.jOverlayMenu_Sidepane);
      this.jSidepane_IFrame = this.jOverlayMenu_Sidepane.find('iframe');
      this.jOverlayMenu_SidepaneButton = $(`<button class="btn btn-sm btn-outline-secondary bg-light" title="Sidepane">
        <i class="fa fa-window-maximize" aria-hidden="true"></i>
        <span class="label">Sidepane</span>
      </button>`);
      this.jOverlayMenu_SidepaneButton.click((e)=> {
        e.stopPropagation();
        e.preventDefault();
        this.jRootElement.toggleClass('sidepane-active');
      });
      this.sidepane = (t) => {
        this.jRootElement.toggleClass('sidepane-active', t);
      };
      this.jOverlayMenu.append(this.jOverlayMenu_SidepaneButton);
    }
  }
  refreshGraph() {
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
      }
    } ).run();
  }
}

window.ColanderDGraph = ColanderDGraph;

/**
 * As side note :
 * A method to compute exactly width against font and text sizes:
'width': (node) => {
    const ctx = document.createElement('canvas').getContext("2d");
    const fStyle = node.pstyle('font-style').strValue;
    const size = node.pstyle('font-size').pfValue + 'px';
    const family = node.pstyle('font-family').strValue;
    const weight = node.pstyle('font-weight').strValue;

    ctx.font = fStyle + ' ' + weight + ' ' + size + ' ' + family;
    return ctx.measureText(node.data('name'));
}
 *
 */
