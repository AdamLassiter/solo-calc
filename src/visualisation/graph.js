var svg = d3.select("svg"),
    width = +svg.attr("width"),
    height = +svg.attr("height");

var color = d3.scaleOrdinal(d3.schemeCategory20);

var simulation = d3.forceSimulation()
    .force("link", d3.forceLink().id(function(d) { return d.id; }))
    .force("charge", d3.forceManyBody())
    .force("x", d3.forceX(width / 2).strength(0.05))
    .force("y", d3.forceY(height / 2).strength(0.05));

d3.json("graph.json", function(error, graph) {
    if (error) throw error;

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

    var link = svg.append("g")
        .attr("class", "links")
        .selectAll(".links")
        .data(graph.graph.edges)
        .enter()
            .append("polyline")
            .attr("stroke-width", function(d) { return Math.sqrt(d.value); })
            .each(function(d) {
                item = d3.select(this).data([d])
                if (d["arrow"] != 0) {
                    item.attr("marker-mid", "url(#mid)");
                }
            });
    
    var node = svg.append("g")
        .attr("class", "nodes")
        .selectAll(".nodes")
        .data(graph.graph.nodes)
        .enter()
            .append("circle")
            .attr("r", 5)
            .attr("fill", function(d) { return color(d.group); })
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

   var box = svg.append("g")
        .attr("class", "boxes")
        .selectAll(".boxes")
        .data(graph.boxes)
        .enter()
            .append("g")
            .attr("class", "box")
            .each(function(d) {
                item = d3.select(this).data([d])
                var perimeter = d.perimeter;
                item.append("g")
                    .attr("class", "nodes")
                    .selectAll(".nodes")
                    .data(d.graph.nodes)
                    .enter()
                        .filter(function(d) {
                            var repeat = false;
                            perimeter.forEach(function(node) {
                                repeat |= node["id"] == d["id"];
                            });
                            return !repeat;
                        })
                        .append("circle")
                        .attr("r", 5)
                        .attr("fill", function(d) { return color(d.group); })
                        .call(d3.drag()
                            .on("start", dragstarted)
                            .on("drag", dragged)
                            .on("end", dragended));
                item.append("g")
                    .attr("class", "links")
                    .selectAll(".links")
                    .data(d.graph.edges)
                    .enter()
                        .append("polyline")
                        .attr("stroke-width", function(d) { return Math.sqrt(d.value); })
                        .each(function(d) {
                            item = d3.select(this).data([d])
                            if (d["arrow"] != 0) {
                                item.attr("marker-mid", "url(#mid)");
                            }
                        });
            });    

    var allNodes = d3.selectAll(".nodes").selectAll(function() { return this.childNodes; }),
        allLinks = d3.selectAll(".links").selectAll(function() { return this.childNodes; }),
        nodesList = [],
        linksList = [];

    allNodes.append("title")
        .text(function(d) { return d.title; });
 
    allNodes.datum(function(d) {
        var repeat = false;
        nodesList.forEach(function(node) {
            repeat |= node["id"] == d["id"];
        });
        if (!repeat) {nodesList.push(d)};
        return d;});
    allLinks.datum(function(d) {linksList.push(d); return d;});

    simulation
        .nodes(nodesList)
        .on("tick", ticked)
        .force("link")
        .links(linksList);

    function ticked() {
        allLinks.attr("x1", function(d) { return d.source.x; })
            .attr("y1", function(d) { return d.source.y; })
            .attr("x2", function(d) { return d.target.x; })
            .attr("y2", function(d) { return d.target.y; });

        allNodes.attr("cx", function(d) { return d.x; })
            .attr("cy", function(d) { return d.y; })
            .attr("r",  function(d) { return d.r; });

        allLinks.attr("points", function(d) {
            var x0 = d.source.x,
                y0 = d.source.y,
                x1 = d.target.x,
                y1 = d.target.y,
                mx = (0.7*d.target.x + 1.3*d.source.x) / 2,
                my = (0.7*d.target.y + 1.3*d.source.y) / 2;
            return x0 + "," + y0 + " " + mx + "," + my + " " + x1 + "," + y1;
        });
    }
});

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
