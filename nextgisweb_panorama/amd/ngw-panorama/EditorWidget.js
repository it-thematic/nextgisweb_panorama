define([
    "dojo/_base/declare",
    "dojo/_base/lang",
    "dojo/_base/array",
    "dojo/json",
    "dojo/dom-style",
    "dojo/dom-class",
    "dojo/store/Memory",
    "dojo/store/Observable",
    "ngw-feature-layer/DisplayWidget",
    "dijit/_TemplatedMixin",
    "dijit/_WidgetsInTemplateMixin",
    "dijit/Toolbar",
    "@nextgisweb/pyramid/api",
    "@nextgisweb/pyramid/i18n!",
    // resource
    "dojo/text!./template/EditorWidget.hbs",
    // template
    "dojox/layout/TableContainer",
    "ngw-file-upload/FileUploader",
    "dijit/form/Button",
    "dijit/form/Textarea",
    "dgrid/OnDemandGrid",
    "dgrid/Keyboard",
    "dgrid/Selection",
    "dgrid/editor",
    "dgrid/extensions/DijitRegistry",
    "dijit/layout/BorderContainer",
    "ngw-pyramid/form/CodeMirror"

], function (
    declare,
    lang,
    array,
    json,
    domStyle,
    domClass,
    Memory,
    Observable,
    DisplayWidget,
    _TemplatedMixin,
    _WidgetsInTemplateMixin,
    Toolbar,
    api,
    i18n,
    template,
    Button,
    Textarea,
    Grid,
    Keyboard,
    Selection,
    editor,
    DijitRegistry,
    BorderContainer
) {

    function fileSizeToString(size) {
        var units = ["B", "KB", "MB", "GB"],
            i = 0;
        while (size >= 1024) {
            size /= 1024;
            ++i;
        }
        return size.toFixed(1) + " " + units[i];
    }

    var GridClass = declare([Grid, Keyboard, Selection, editor, DijitRegistry], {
        columns: [
            {
                field: "display_name",
                label: i18n.gettext("Display name"),
                sortable: false
            },
            {
                field: "keyname",
                label: i18n.gettext("Keyname"),
                sortable: true,
                autoSave: true,
                editor: "text",
                editOn: "dblclick"
            }
        ]
    });

    return declare([DisplayWidget, _TemplatedMixin, _WidgetsInTemplateMixin], {
        title: i18n.gettext("Panorama"),
        templateString: i18n.renderTemplate(template),
        prefix: "panorama",

        constructor: function () {
            this.inherited(arguments);
            this.store = new Observable(new Memory({idProperty: "lid"}));
        },

        _getValueAttr: function () {
            this.inherited(arguments);
            var value = {};
            value['panorama'] = json.stringify(json.parse(this.wPanorama.get("value")));

            value['scenes'] = [];
            this.store.query().forEach(function (f) {
                var c = lang.clone(f);
                c.lid = undefined;
                value['scenes'].push(c);
            })

            return value;
        },

        _setValueAttr: function (data) {
            this.inherited(arguments);
            this.wPanorama.set("value", json.stringify(data.panorama, null, 4));

            var store = this.store;
            store.query().forEach( function (itm) {
                store.remove(itm.lid);
            });

            array.forEach(data.scenes, (itm) => {
                var value = lang.clone(itm);
                this.store.add(value);
            }, this);
        },

        buildRendering: function () {
            this.inherited(arguments);

            domClass.add(this.wScenes.domNode, "ngw-feature-attachment-EditorWidget");

            this.grid = new GridClass({store: this.store});
            domClass.add(this.grid.domNode, "dgrid-border-fix");
            domStyle.set(this.grid.domNode, "border", "none");
            this.wScenes.addChild(this.grid);


            this.btnUpload.on("complete", lang.hitch(this, function (data) {
                var panorama = json.parse(this.wPanorama.get("value")) || [];

                array.forEach(data.upload_meta, (element) => {
                    this.store.put({
                        display_name: element.name,
                        keyname: element.name,
                        file_upload: {
                            id: element.id,
                            name: element.name,
                            mime_type: element.mime_type
                        }
                    });
                    if (panorama.length === 0) {
                        panorama.push({
                            id: element.name,
                            name: element.name,
                            links:[]
                        });
                        return
                    }

                    if (!!!panorama[panorama.length - 1].links) {
                        panorama[panorama.length - 1].links = [];
                    }
                    panorama[panorama.length - 1].links.push({ nodeId: element.name});

                    panorama.push({
                        id: element.name,
                        name: element.name,
                        links: [
                            { nodeId: panorama[panorama.length - 1].id}
                        ]
                    })

                }, this);
                this.wPanorama.set("value", json.stringify(panorama, null, 4));
            }));

            this.btnDelete.on('click', lang.hitch(this, function () {
                var panorama = json.parse(this.wPanorama.get("value") || []);
                for (var key in this.grid.selection) {
                    var nodeId = this.store.get(key).keyname;
                    panorama = panorama.filter((itm) => itm.id !== nodeId);
                    panorama.forEach((elem) => {
                        if (!!!elem.links) { return; }
                        elem.links = elem.links.filter((itm) => itm.nodeId !== nodeId);
                    })
                    this.store.remove(key);
                }
                this.wPanorama.set("value", json.stringify(panorama, null, 4));
            }));

            this.btnBeautify.on('click', lang.hitch(this, function () {
                this.wPanorama.set("value", json.stringify(json.parse(this.wPanorama.get("value")), null, 4))
            }));

            console.log('ngw-panorama/EditorWidget: buildRendering');
        }
    });
});