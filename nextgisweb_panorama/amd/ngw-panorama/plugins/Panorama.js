define([
    "dojo/_base/declare",
    "dojo/_base/lang",
    "dojo/topic",
    "dijit/layout/BorderContainer",
    "dijit/form/Button",
    "dijit/layout/TabContainer",
    'ngw-webmap/ol/layer/Vector',
    "openlayers/ol",
    "ngw-webmap/plugin/_PluginBase",
    "@nextgisweb/pyramid/api",
    "@nextgisweb/pyramid/i18n!",
    "@nextgisweb/pyramid/psv"
], function (
    declare,
    lang,
    topic,
    BorderContainer,
    Button,
    TabContainer,
    Vector,
    ol,
    _PluginBase,
    api,
    i18n,
    psv,
) {
    const BOY_ICON = 'data:image/png;base64,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'

    var Panorama = declare([BorderContainer], {
        closable: true,
        gutters: false,
        iconClass: "iconMap",

        _panoListeners: [],

        constructor: function (options) {
            declare.safeMixin(this, options);
            this._map = options.plugin.display.map;
            this._overlay = new Vector('panorama_point', {
                title: 'Pointer',
                style: this._getDefaultStyle()
            });
            this._overlay.olLayer.setZIndex(1000);
            this._source = this._overlay.olLayer.getSource();
            this._map.addLayer(this._overlay);
        },

        postCreate: function () {
            this.inherited(arguments);
            this._bindEvents();
        },

        destroy: function () {
            this._source.clear();
            delete this.viewer;
            this._panoListeners.forEach(itm => itm.remove());
            this.inherited(arguments);
        },

        _layoutChildren: function () {
            this.inherited(arguments);
            if (!!this._timerResize) {
                clearTimeout(this._timerResize);
            }
            this._timerResize = setTimeout(() => {
                if (!!!this.viewer) {
                    return;
                }
                this.viewer.autoSize();
            }, 500);
        },

        _getDefaultStyle: function () {
            return new ol.style.Style({
                image: new ol.style.Icon({
                    opacity: 1,
                    src: BOY_ICON
                })
            });
        },

        initialize_viewer: function (nodes, point) {
            if (!!!this.viewer) {
                this.viewer = new psv.PSV.Viewer({
                    caption: this.title,
                    container: this.domNode,
                    plugins: [
                        psv.CP.CompassPlugin,
                        [psv.VTP.VirtualTourPlugin, {
                            positionMode: psv.VTP.MODE_GPS,
                            renderMode: psv.VTP.MODE_3D,
                            nodes: nodes,
                            linksOnCompass: true
                        }],
                    ]
                });
                this._bindPanoramaEvents();
            } else {
                let vt = this.viewer.getPlugin(psv.VTP.VirtualTourPlugin);
                vt.setNodes(nodes);
            }
            var initPosition = ol.proj.transform(point, 'EPSG:3857', 'EPSG:4326');
            var arrayOfDistances = [];
            nodes.forEach(node => {
                let distance = ol.sphere.getDistance(initPosition, node.position);
                arrayOfDistances.push({distance: distance, node: node});
            });
            arrayOfDistances.sort((a, b) => a.distance - b.distance);
            let vt = this.viewer.getPlugin(psv.VTP.VirtualTourPlugin);
            vt.setCurrentNode(arrayOfDistances[0].node.id);
        },

        _bindEvents: function () {
            this._panoListeners.push(topic.subscribe("panorama.open", lang.hitch(this, this.loadPanoramaOfFeature)));
        },

        _bindPanoramaEvents: function () {
            var vtp = this.viewer.getPlugin(psv.VTP.VirtualTourPlugin);
            vtp.on('node-changed', lang.hitch(this, this._onPanoramaNodeChange));
        },

        _onPanoramaNodeChange: function (e, nodeId, data) {
            this._source.clear();
            // Установка маркера
            let vtp = this.viewer.getPlugin(psv.VTP.VirtualTourPlugin);
            let node = vtp.datasource.nodes[nodeId];
            let coord = ol.proj.transform(node.position, 'EPSG:4326', 'EPSG:3857')
            let point = new ol.geom.Point(coord);
            this._source.addFeature(new ol.Feature({geometry: point}));

            let nextLink = this._calculateNextNode(node, data);
            if (!!!nextLink) {return; }

            let nextPoint = nextLink.position;
            let currentPoint = node.position;
            // Расчёт угла поворота от оси Х направленной вверх к следующей панорама с началом отсчёта в текущей точке
            let dy = nextPoint[0] - currentPoint[0], dx = nextPoint[1] - currentPoint[1];
            let rotationAngle = Math.atan2(dy, dx);
            this.viewer.rotate({longitude: rotationAngle, latitude: 0});
        },

        _calculateNextNode: function (node, data) {
            /*
            data.fromNode - с какой панорамы перешли
            data.fromLink - на какую ссылку нажимали при переходе
            data.fromLinkPosition - какие были координаты link
             */
            let previousLink = data.fromNode;
            let links = [...node.links];

            if (!previousLink || links.length === 1) { return links[0]; }

            let indexOfPreviousLink = links.findIndex(item => item.nodeId === previousLink.id);
            if (indexOfPreviousLink !== undefined) { links.splice(indexOfPreviousLink, 1); }
            return links[0];
        },

        loadPanoramaOfFeature: function (e) {
            var layerId = e.layerId, featureId = e.featureId, point = e.point, widget = this;
            if (!!!layerId || !!!featureId) { return; }

            api.route('feature_panorama.item', {id: layerId, fid: featureId})
                .get()
                .then(lang.hitch(this, (data) => {
                    (data !== null) && (data.length > 0) ? widget.initialize_viewer(data, point) : null
                }))
        }
    });

    return declare([_PluginBase], {

        constructor: function () {
            var plugin = this;

            this.menuItem = new Button({
                label: i18n.gettext("Panorama"),
                showLabel: false,
                iconClass: "material-icons material-icons-enable",
                "data-icon": "panorama",
                _setIconClassAttr: { node: "titleNode", type: "class" },
                disabled: true,
                onClick: function () {
                    plugin.openPanorama();
                }
            });

            this.tabContainer = new TabContainer({
                region: "bottom",
                style: "height: 35%",
                splitter: true,
            });

            this.display.watch("item", function (attr, oldVal, newVal) {
                var itemConfig = plugin.display.get("itemConfig");
                if (itemConfig.type !== 'layer') {
                    plugin.menuItem.set("disabled", true);
                } else {
                    api.route('resource.panorama.check', {id: itemConfig.layerId})
                        .get()
                        .then(lang.hitch(this, function (data) {
                            plugin.menuItem.set("disabled", data.count === 0);
                        }));
                }
            });
        },

        postCreate: function () {
            if (this.display.layersPanel && this.display.layersPanel.contentWidget.toolbarMenu) {
                this.display.layersPanel.contentWidget.toolbarMenu.addChild(this.menuItem);
            }

        },

        openPanorama: function () {
            var item = this.display.dumpItem(), layerId = item.layerId;

            if (!!!this.pane) {
                this.pane = this._buildPane(layerId, item);
                if (!this.tabContainer.getChildren().length) {
                    this.display.mapContainer.addChild(this.tabContainer);
                }
                this.tabContainer.addChild(this.pane);
                this.tabContainer.selectChild(this.pane);
            }
        },

        _buildPane: function (layerId, item) {

            return new Panorama({
                title: item.label,
                plugin: this,
                onClose: lang.hitch(this, function () {
                    delete this.pane;
                    if (this.tabContainer.getChildren().length == 1) {
                        this.display.mapContainer.removeChild(this.tabContainer);
                    }
                    return true;
                }),
            });
        },
    });
});
