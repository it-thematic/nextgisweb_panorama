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
    var Panorama = declare([BorderContainer], {
        closable: true,
        gutters: false,
        iconClass: "iconMap",

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
            var strokeStyle = new ol.style.Stroke({
                width: 3,
                color: 'rgba(255б 0, 0, 1)'
            });

            return new ol.style.Style({
                stroke: strokeStyle,
                image: new ol.style.Circle({
                    stroke: strokeStyle,
                    radius: 5
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
            topic.subscribe("panorama.open", lang.hitch(this, this.loadPanoramaOfFeature));
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

            this.plugin.display.featureHighlighter._highlightFeature({olGeometry: point});
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

        pano: null,

        constructor: function () {
            var plugin = this;

            this.menuItem = new Button({
                label: i18n.gettext("Panorama"),
                showLabel: false,
                iconClass: "material-icons material-icons-enable icon-panorama",
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
