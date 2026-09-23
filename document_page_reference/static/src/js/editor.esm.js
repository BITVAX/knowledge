/* @odoo-module */

import {HtmlField, htmlField} from "@web/views/fields/html/html_field";
import {onMounted, onPatched, useRef} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

class DocumentPageReferenceField extends HtmlField {
    // The base web.HtmlField of Odoo 18 renders the readonly value in a
    // bare <span t-out> with no ref, so `readonlyElementRef` never exists
    // and the links stay unbound: own template with the ref.
    static template = "document_page_reference.HtmlField";

    setup() {
        super.setup();
        this.orm = useService("orm");
        this.action = useService("action");
        this.readonlyElementRef = useRef("readonlyElement");
        this._onClickDirectLink = this._onClickDirectLink.bind(this);
        onMounted(() => this._bindLinks());
        onPatched(() => this._bindLinks());
    }
    _bindLinks() {
        const el = this.readonlyElementRef && this.readonlyElementRef.el;
        if (!el) return;
        // Remove target="_blank" from internal reference links
        // (added by retargetLinks in HtmlField)
        for (const link of el.querySelectorAll("a.oe_direct_line")) {
            link.removeAttribute("target");
            link.removeAttribute("rel");
            link.removeEventListener("click", this._onClickDirectLink);
            link.addEventListener("click", this._onClickDirectLink);
        }
    }
    _onClickDirectLink(event) {
        event.preventDefault();
        event.stopPropagation();
        const target = event.currentTarget;
        const model = target.dataset.oeModel;
        const id = parseInt(target.dataset.oeId, 10);
        if (!model || !id) return;
        this.orm.call(model, "get_formview_action", [[id]], {}).then((action) => {
            this.action.doAction(action);
        });
    }
}
registry.category("fields").add("document_page_reference", {
    ...htmlField,
    component: DocumentPageReferenceField,
});
