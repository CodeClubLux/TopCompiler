function main_nodeInit(){var d=0;return function c(b){while(1){switch (d){case 0:http_nodeInit();main__read = server_readFile;main_quit = process.exit;main_server = http_server(main_requestHandler);d=5;return (main_server).listen(http_port,c);case 5:log((((("started web server on port ")+((http_port)).toString()))+("").toString()));html_nodeInit();main_style= typeof html_style=='undefined'||html_style;main_onClick= typeof html_onClick=='undefined'||html_onClick;main_comp= typeof html_comp=='undefined'||html_comp;main_mapView= typeof html_mapView=='undefined'||html_mapView;main_toEffect= typeof html_toEffect=='undefined'||html_toEffect;main_data = newVector(new main_Data(main_Male,"blue","blue"),new main_Data(main_Male,"blue","blue"),new main_Data(main_Female,"pink","pink"),new main_Data(main_Female,"red","red"));main_unique = main_for.bind(null,((function(main_elem, main_indiv){;return (function(){if((!((main_indiv).has(main_elem)))){return [(Some(main_elem)),(main_indiv).append(main_elem)];}
else{return [None,main_indiv];}})();})),EmptyVector);main_add = (function(main_a, main_b){;return ((main_a+main_b)|0);});;return;}}}()}var main__read;var main_quit;var main_server;var main_data;var main_unique;var main_add;var main_h1;var main_span;var main_p;var main_br;var main_button;var main_app;var main_div;var main_style;var main_render;var main_onClick;var main_comp;var main_mapView;var main_toEffect;function main_read(main_path,c){var main_Some;var main_x;var main_None;var g=0;return function f(d){while(1){switch(g){case 0:g=1;return main__read(main_path,f);case 1:;return c(function(){var h=d; if (h[0]==0){var main_x=h[1];return main_x;} if (h[0]==1){log(("cannot find file, "+main_path));return main_quit(1);}}());}}}()}function main_requestHandler(main_req,c){var main_Some;var main_content;var main_None;var g=0;return function f(d){while(1){switch(g){case 0:log(("request, "+(main_req).url));var h=(main_req).url; if (h=="/"){g=3;return main__read("EC.html",f);}/*case*/g=4;break;/*case*/case 3:d=function(){var j=d; if (j[0]==0){var main_content=j[1];return core_assign(http_response,{body:main_content,contentType:"text/html"});} if (j[0]==1){return core_assign(http_response,{status:404});}}();g=2;/*block*/break;/*if*/case 4:/*notif*/ if (1){d=core_assign(http_response,{status:404,body:"404 Page not found"});g=2;/*block*/break;}case 2:;return c(d);}}}()}var main_Male=[0,];var main_Female=[1,];function main_Data(c,d){this.gender=c;this.color=d;}main_Data.fields=["gender","color"];function main_for(main_func, main__state, main_arr){var main_state;main_state = main__state;var main_new;main_new = EmptyVector;var main_length;main_length = (main_arr).length;var main_i;main_i = 0;
while((main_i<main_length)){var main_tx;main_tx = main_func(main_arr.get(main_i),main_state);var main_t;main_t = (main_tx)[0];main_state=(main_tx)[1];main_new=function(){var c=main_t; if (c[0]==0){var main_tmp=c[1];return (main_new).append(main_tmp);} if (c[0]==1){return main_new;}}();main_i=((main_i+1)|0);};return main_new;}function main_categorize(main_arr){var main_colors;main_colors = main_unique((main_arr).map((function(main_i){;return (main_i).color;})));function main_transform(main_c){;return [main_c,(((main_arr).filter((function(main_i){;return function(){var c=(main_i).gender; if (c[0]==0){return ((main_i).color===main_c);} if (1){return false;}}();})))).length,(((main_arr).filter((function(main_i){;return function(){var d=(main_i).gender; if (d[0]==1){return ((main_i).color===main_c);} if (1){return false;}}();})))).length];};return (main_colors).map(main_transform);}function main_r(main_i){function main_func(main_elem, main_state){;return [(Some(((main_elem-main_state)|0))),main_elem];};return main_for(main_func,main_i.get(0),(main_i).slice(1,(main_i).length));}