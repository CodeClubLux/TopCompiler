function http_clientInit(){var d=0;return function c(b){while(1){switch (d){case 0:http_response = new http_Response(200,"text/plain","","");http_get = _http_get;;return;}}}()}var http_response;var http_get;function http_Server(c){this.listen=c;}http_Server.fields=["listen"];function http_NodeHTTP(c){this.createServer=c;}http_NodeHTTP.fields=["createServer"];function http_Request(c){this.url=c;}http_Request.fields=["url"];function http_Response(c,d,f){this.status=c;this.contentType=d;this.body=f;}http_Response.fields=["status","contentType","body"];http_Response.prototype.toString=(function(){return http_Response_toString(this)});function http_Response_toString(http_self){;return (((((((((((("Response(")+(((http_self).status)).toString()))+(", ").toString()))+(((http_self).contentType)).toString()))+(", ").toString()))+(((http_self).body)).toString()))+(")").toString());}function http_endResponse(http_x){;return core_assign(http_response,{body:jsonStringify(http_x)});}function http_toUrl(http_expects){;return ("query/"+jsonStringify(http_expects(http_endResponse)));}function http_query(http_fromJSON, http_expects,c){var http_url;var http_body;var g=0;return function f(d){while(1){switch(g){case 0:http_url = http_toUrl(http_expects);g=1;return http_get(http_url,f);case 1:http_body = ((d)).body;;return c(http_fromJSON(http_body));}}}()}