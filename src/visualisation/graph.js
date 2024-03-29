var margin = {top: 20, right: 20, bottom: 20, left: 20},
    width = 800 - margin.left - margin.right,
    height = 900 - margin.top - margin.bottom;

var svg = d3.select("body")
    .append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
    .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

var color = d3.scaleOrdinal(d3.schemeCategory10);

var simulation = d3.forceSimulation()
    .force("link", d3.forceLink().id(function(d) { return d.id; }))
    .force("charge", d3.forceManyBody())
    .force("x", d3.forceX(width / 2).strength(0.03))
    .force("y", d3.forceY(height / 2).strength(0.03));

function svgLink(svgElem, dataJoin, filterBy) {
    svgElem.append("g")
        .attr("class", "links")
        .selectAll(".links")
        .data(dataJoin)
        .enter()
            .filter(filterBy)
            .append("g")
            .attr("class", "edge")
            .selectAll("*")
            .data(function(d) { return d; })
            .enter()
                .append("polyline")
                .attr("stroke-width", function(d) { return Math.sqrt(d.value); })
                .each(function(d) {
                    item = d3.select(this).data([d]);
                    if (d["arrow"] != 0) {
                        item.attr("marker-mid", "url(#mid)");
                    }
                });
}

function svgNode(svgElem, dataJoin, filterBy) {
   svgElem.append("g")
        .attr("class", "nodes")
        .selectAll(".nodes")
        .data(dataJoin)
        .enter()
            .filter(filterBy)
            .append("circle")
            .attr("fill", function(d) { return color(d.group); })
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));
}

function containedIn(list) {
    return function(item) {
        var repeat = false;
        list.forEach(function(node) {
            repeat |= node["id"] == item["id"];
        });
        return repeat;
    };
}

function maintainPosition(oldElems) {
    return function(elem) {
        var oldElem = oldElems.find(function(d) { return d.id == elem.id; });
        if (oldElem != undefined) {
            elem.x = oldElem.x;
            elem.y = oldElem.y;
        }
    };
}

var oldGraph;
function updateData(graph) {
    if (oldGraph != undefined) {
        graph.graph.nodes.forEach(maintainPosition(oldGraph.graph.nodes));
        graph.boxes.forEach(function(box) {
            var oldBox = oldGraph.boxes.find(function(d) { return d.id == box.id; });
            if (oldBox != undefined) {
                box.graph.nodes.forEach(maintainPosition(oldBox.graph.nodes));
                box.perimeter.forEach(maintainPosition(oldBox.perimeter));
            }
        });
    }

    oldGraph = graph
    svg.selectAll("*").remove()

    var arrow = svg.append("svg:defs")
        .selectAll("marker")
        .data(["mid"])
        .enter()
            .append("svg:marker")
            .attr("id", String)
            .attr("viewBox", "0 -5 10 10")
            .attr("markerWidth", 10)
            .attr("markerHeight", 10)
            .attr("orient", "auto")
            .append("svg:path")
            .attr("d", "M0,-5 L10,0 L0,5");

    var linkList = graph.graph.edges,
        link = svgLink(svg, linkList, function(d) { return true; });
    
    var nodeList = graph.graph.nodes,
        node = svgNode(svg, nodeList, function(d) { return true });
    
    function allNodes() {
        return d3.selectAll(".nodes").selectAll(function() { return this.childNodes; });
    };
    function allNodesList() {
        var nodes = [];
        function nodeGather(d) {
            containedIn(nodes)(d) ? null : nodes.push(d);
            return d;
        };
        allNodes().datum(nodeGather);
        return nodes;
    };
    
    var box = svg.append("g")
        .attr("class", "boxes")
        .selectAll(".boxes")
        .data(graph.boxes)
        .enter()
            .append("g")
            .attr("class", "box")
            .each(function(d) {
                item = d3.select(this).data([d])
                svgNode(item, d.graph.nodes, function(_d) { return !containedIn(d.perimeter)(_d); });
                svgNode(svg, d.perimeter, function(d) { return !containedIn(allNodesList())(d); });
                svgLink(item, d.graph.edges, function(d) { return true });
           });

    var allLinks = d3.selectAll(".edge").selectAll(function() { return this.childNodes; }),
        allBoxes = d3.selectAll(".boxes").selectAll(function() { return this.childNodes; }),
        allLinksList = [];

    allNodes().append("title")
        .text(function(d) { return d.title; });

    //allBoxes.datum(function(d) { d.perimeter.forEach(nodeGather); return d; });
    allLinks.datum(function(d) { allLinksList.push(d); return d; });

    allNodesList().forEach(function(d) {
        d.x = (d.x == undefined)? width / 2 : d.x;
        d.y = (d.y == undefined)? height / 2 : d.y;
    });

    simulation
        .nodes(allNodesList())
        .on("tick", ticked)
        .force("link")
        .links(allLinksList);

    function ticked() {
        allLinks
            .attr("x1", function(d) { return d.source.x; })
            .attr("y1", function(d) { return d.source.y; })
            .attr("x2", function(d) { return d.target.x; })
            .attr("y2", function(d) { return d.target.y; })
            .attr("points", function(d) {
                var x0 = d.source.x,
                    y0 = d.source.y,
                    x1 = d.target.x,
                    y1 = d.target.y,
                    mx = (0.7*x1 + 1.3*x0) / 2,
                    my = (0.7*y1 + 1.3*y0) / 2;
                return x0 + "," + y0 + " " + mx + "," + my + " " + x1 + "," + y1;
            });

        allNodes()
            .attr("cx", function(d) { return d.x; })
            .attr("cy", function(d) { return d.y; })
            .attr("r",  function(d) { return d.r; });
    }
    simulation.alphaTarget(0.1).restart();
}

var json;
function getJSON() {
    if (json != undefined) {
        jQuery.ajax({
            type: "POST",
            url: "http://localhost:8001",
            data: JSON.stringify(json),
            cache: false,
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(data) { json = data; updateData(json); },
            failure: function(err) { alert(err); }
        });
    } else {
        jQuery.ajax({
            type: "GET",
            url: "http://localhost:8001",
            cache: false,
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(data) { json = data; updateData(json); },
            failure: function(err) { alert(err); }
        });
    }
}
getJSON();

function reduce() {
    getJSON();
}

function dragstarted(d) {
    if (!d3.event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
}

function dragged(d) {
    d.fx = d3.event.x;
    d.fy = d3.event.y;
}

function dragended(d) {
    if (!d3.event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
}
