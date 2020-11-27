odoo.define('website_searchapp', function (require) {

    var ajax = require('web.ajax');
    var core = require('web.core');
    var qweb = core.qweb;

    ajax.loadXML('/website_searchapp/static/qweb/snippets.xml', qweb);

    jQuery(document).ready(function ($) {
        var jqxhr = {
            abort: function () {
            }
        };
        var loader = {
            load: function () {
                if ($(".search-autocomplete #search-loader").length) {
                    $(".search-autocomplete").show();
                    $(".search-autocomplete #search-loader").show();
                } else {
                    $(".search-autocomplete").prepend("<div id='search-loader'><div class='lds-ellipsis'><div></div><div></div><div></div><div></div></div></div>").show();
                }
            }
        };
        jQuery("#search-input").keyup(function (event) {
            var name = jQuery(this).val();
            var $autocomplete = jQuery("#search_autocomplete");
            var separateSearch = name.replace(/[^a-z0-9\s]/gi, ' ').replace(/[_\s]/g, ' ');
            var keycode = (event.keyCode ? event.keyCode : event.which);

            if (!$autocomplete.length) {
                $(this).after('<div id="search_autocomplete"><div class="search-autocomplete"></div></div>');
            }
            jqxhr.abort();
            if (keycode == '13') {
                window.location.replace("/search?q=" + name);
            }
            if (keycode == '27') {
                $(".search-autocomplete").hide();
            }

            if (name.length < 3) {
                $(".search-autocomplete").html("").hide();
                jqxhr.abort()
            } else {
                loader.load();
                jqxhr = $.ajax({
                    type: "POST",
                    dataType: "json",
                    url: "/searchapp/index/",
                    contentType: "application/json; charset=utf-8",
                    data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'q': name}}),
                    success: function (data) {
                        $(".search-autocomplete").html("").append(qweb.render("website_searchapp.search_autocompletev2", {
                            search_data: data,
                            search_query: name
                        })).show(
                            function () {
                                $(".search-autocomplete ul li").mark(separateSearch, {
                                    "element": "span",
                                    "className": "highlight",
                                    "useWildcards": true
                                });
                                $("span.rating").each(function () {
                                    $(this).starRating({
                                        totalStars: 5,
                                        initialRating: 4.5,
                                        readOnly: true,
                                        useGradient: false,
                                        strokeWidth: 0,
                                        starSize: 18
                                    });
                                });
                            }
                        );
                        queryLogs(name);
                    }
                });
            }

            $('#search-input').keypress(function (event) {
                var name = $(this).val();
                var keycode = (event.keyCode ? event.keyCode : event.which);
                if (keycode == '13') {
                    window.location.replace("/search?q=" + name);
                }

                if (keycode == '27') {
                    $(".search-autocomplete").hide();
                }

            });

        });

        $(document).mouseup(function (e) {
            var container = new Array();
            container.push($('#search-input'));

            $.each(container, function (key, value) {
                if (!$(value).is(e.target)
                    && $(value).has(e.target).length === 0)
                {
                    $(".search-autocomplete").hide();
                }
            });
        });

        $('#search-input').focus(function () {
            var val = $(this).val();
            if (val.length < 3) {
                $(".search-autocomplete").hide();
            } else {
                $(".search-autocomplete").show();
            }
        });

        queryLogs = function (q) {
            $.ajax({
                type: "POST",
                dataType: "json",
                url: "/searchapp/index/query",
                contentType: "application/json; charset=utf-8",
                data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'idx_count': indexCount, 'q': q}}),
                success: function () {
                }
            });
        }

    });
});
