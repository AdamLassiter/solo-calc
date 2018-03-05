var svg = d3.select("svg"),
    width = +svg.attr("width"),
    height = +svg.attr("height");

var color = d3.scaleOrdinal(d3.schemeCategory20);

var simulation = d3.forceSimulation()
    .force("link", d3.forceLink().id(function(d) { return d.id; }))
    .force("charge", d3.forceManyBody())
    .force("center", d3.forceCenter(width / 2, height / 2));

d3.json("graph.json", function(error, graph) {
    if (error) throw error;

    var arrow = svg.append("svg:defs").selectAll("marker")
            .data(["end"])
        .enter()
            .append("svg:marker")
            .attr("id", String)
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 25)
            .attr("refY", 0)
            .attr("markerWidth", 10)
            .attr("markerHeight", 10)
            .attr("orient", "auto")
        .append("svg:path")
            .attr("d", "M0,-5 L10,0 L0,5");

    var link = svg.append("g")
        .attr("class", "links")
        .selectAll("lines")
        .data(graph.graph.edges)
        .enter()
            .append("line")
            .attr("stroke-width", function(d) { return Math.sqrt(d.value); })
            .each(function(d) {
                item = d3.select(this).data([d])
                if (d["arrow"] != 0) {
                    item.attr("marker-end", "url(#end)");
                }
            });

    var node = svg.append("g")
        .attr("class", "nodes")
        .selectAll("nodes")
        .data(graph.graph.nodes)
        .enter()
            .append("circle")
            .attr("r", 5)
            .attr("fill", function(d) { return color(d.group); })
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

    node.append("title")
        .text(function(d) { return d.id; });

    simulation
        .nodes(graph.graph.nodes)
        .on("tick", ticked);

    simulation.force("link")
        .links(graph.graph.edges);

    function ticked() {
        link
            .attr("x1", function(d) { return d.source.x; })
            .attr("y1", function(d) { return d.source.y; })
            .attr("x2", function(d) { return d.target.x; })
            .attr("y2", function(d) { return d.target.y; });

        node
            .attr("cx", function(d) { return d.x; })
            .attr("cy", function(d) { return d.y; })
            .attr("r",  function(d) { return d.r; });
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
