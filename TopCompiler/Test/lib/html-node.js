function html_nodeInit(){var d=0;return function c(b){while(1){switch (d){case 0:;;;html_changeName = _html_changeName;html_style = html_newAttrib.bind(null,"style");html_placeHolder = html_newAttrib.bind(null,"placeholder");html_position = html_newAttrib.bind(null,"position");html__type = html_newAttrib.bind(null,"type");html_height = html_newAttrib.bind(null,"height");html_width = html_newAttrib.bind(null,"width");html_id = html_newAttrib.bind(null,"id");html_min = html_newAttrib.bind(null,"min");html_max = html_newAttrib.bind(null,"max");html_step = html_newAttrib.bind(null,"step");html_value = html_newAttrib.bind(null,"value");html_href = html_newAttrib.bind(null,"href");html_src = html_newAttrib.bind(null,"src");html_kind = html_newAttrib.bind(null,"type");html__float = html_newAttrib.bind(null,"float");html_class = html_newAttrib.bind(null,"className");html_noAttrib = EmptyVector;;return;}}}()}var html_changeName;var html_style;var html_placeHolder;var html_position;var html__type;var html_height;var html_width;var html_id;var html_min;var html_max;var html_step;var html_value;var html_href;var html_src;var html_kind;var html__float;var html_class;var html_noAttrib;function html_PosAtom(c,d){this.a=c;this.pos=d;}html_PosAtom._fields=["a","pos"];html_PosAtom.prototype.unary_read=(function(c){return html_PosAtom_unary_read(this,c)});function html_PosAtom_unary_read(html_self,d){var h=0;return function g(f){while(1){switch(h){case 0:;h=1;return (html_self).a.unary_read(g);case 1:;;return d(((html_self).pos).query(f));}}}()}html_PosAtom.prototype.toString=(function(){return html_PosAtom_toString(this)});function html_PosAtom_toString(html_self){;var html_a;html_a = toString((html_self).a);var html_pos;html_pos = toString((html_self).pos);;return (html_a+html_pos);}html_PosAtom.prototype.op_set=(function(c,d){return html_PosAtom_op_set(this,c,d)});function html_PosAtom_op_set(html_self, html_new,f){var j=0;return function h(g){while(1){switch(j){case 0:;;j=2;return (html_self).a.unary_read(h);case 2:;j=3;return ((html_self).a).op_set(((html_self).pos).set(g,html_new),h);case 3:;return f();}}}()}html_PosAtom.prototype.watch=(function(c,d){return html_PosAtom_watch(this,c,d)});function html_PosAtom_watch(html_self, html_f,f){var j=0;return function h(g){while(1){switch(j){case 0:;;function html_func(html_x,k){var n=0;return function m(l){while(1){switch(n){case 0:;n=4;return (html_self).a.unary_read(m);case 4:;n=5;return html_f(((html_self).pos).query(l),m);case 5:;return k();}}}()}j=6;return ((html_self).a).watch(html_func,h);case 6:;return f();}}}()}function html_comp(html_func){;;return html_func;}function html_Event(c){this.target=c;}html_Event._fields=["target"];function html_Attribute(c,d){this.name=c;this.value=d;}html_Attribute._fields=["name","value"];function html_newAttrib(html_name, html_value){;;;return new html_Attribute(html_name,html_value,html_value);}function html_ignoreAct(html_name, html_f){;;function html_func(html_x, html_y,c){var g=0;return function f(d){while(1){switch(g){case 0:;;g=20;return html_f(html_x,f);case 20:;return c(d);}}}()};return html_changeName(html_func,html_name);}function html_withId(html_f){;function html_func(html_id, html_m, html_e,c){var html_res;var g=0;return function f(d){while(1){switch(g){case 0:;;;g=21;return html_f(html_m.get(html_id),html_e,f);case 21:html_res = (d);;return c((html_m).set(html_id,html_res));}}}()};return html_func;}function html_mapWithId(html_v, html_arr, html_a){;;;function html_func(html_id){;;return html_v(html_arr.get(html_id),html_id,html_a);};return (newVectorRange(0,(html_arr).length)).map(html_func);}function html_toEffect(html_name, html_f){;;function html_func(html_x, html_ev,c){var g=0;return function f(d){while(1){switch(g){case 0:;;;return c(html_f(html_x,html_ev));}}}()};return html_changeName(html_func,html_name);}function html_mapView(html_v, html_model, html_a){;;;function html_mapper(html_idx){;var html_result;html_result = html_model.get(html_idx);var html_pos;html_pos = (newLens(function(c){return c.get(html_idx)}, function(d,c){return d.set(html_idx,c)},''+"["+html_idx+"]"));var html_newA;html_newA = new html_PosAtom(html_a,html_pos,html_pos);;return html_v(html_result,html_newA);};return (newVectorRange(0,(html_model).length)).map(html_mapper);}function html_viewFromLens(html_v, html_model, html_pos, html_a){;;;;;return html_v(((html_pos).query(html_model)),new html_PosAtom(html_a,html_pos,html_pos));}function html_get(c){var g=0;return function f(d){while(1){switch(g){case 0:;return c();}}}()}