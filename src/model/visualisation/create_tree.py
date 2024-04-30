import json

import networkx as nx
from bs4 import BeautifulSoup
from community import community_louvain
from pyvis.network import Network
import seaborn as sns
import matplotlib.colors as mcolors


def add_nodes_edges(graph, data, parent=None, skip_frequency_vector=False):
    """
    Add nodes and edges to the graph recursively.
    :param graph:
    :param data:
    :param parent:
    :param skip_frequency_vector:
    :return:
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if skip_frequency_vector and key == "frequency_vector":
                continue
            graph.add_node(key)
            if parent:
                graph.add_edge(parent, key)
            add_nodes_edges(graph, value, key)

def add_title_description(html_file_path, title, description):
    """
    Add a title and description to the right of the graph in the HTML file.
    :param html_file_path:
    :param title:
    :param description:
    :return:
    """

    # Read the HTML file content
    with open(html_file_path, 'r', encoding='utf-8') as html_file:
        html_content = html_file.read()

    # Parse HTML using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the graph container div
    graph_div = soup.find(id="mynetwork")
    if not graph_div:
        print("Graph container not found!")
        return

    # Create new HTML elements for title and description
    title_tag = soup.new_tag("h2")
    title_tag.string = title
    description_tag = soup.new_tag("p")
    description_tag.append(BeautifulSoup(description, 'html.parser'))

    # Check if graph_div's parent has the right style for flex display
    parent_div = graph_div.parent
    if parent_div and 'style' in parent_div.attrs and "display: flex;" in parent_div['style']:
        # Create and append right div directly into the parent div
        right_div = soup.new_tag("div", style="flex: 1; padding: 20px;")
        right_div.append(title_tag)
        right_div.append(description_tag)
        parent_div.append(right_div)
    else:
        # If not correctly styled, create a new container
        new_container = soup.new_tag("div", style="display: flex;")
        new_container.append(graph_div)
        right_div = soup.new_tag("div", style="flex: 1; padding: 20px;")
        right_div.append(title_tag)
        right_div.append(description_tag)
        new_container.append(right_div)
        if parent_div:
            parent_div.replace_with(new_container)
        else:
            soup.body.append(new_container)

    # Write the modified HTML content back to the file
    with open(html_file_path, 'w', encoding='utf-8') as file:
        file.write(str(soup))


def create_tree(data, file_name_export, type="community", skip_frequency_vector=True):
    """
    Create a tree network visualization from the data and save it to an HTML file.
    :param data:  The data to visualize as a tree.
    :param file_name_export:  The name of the HTML file to save the visualization to.
    :param type:  The type of visualization to create. Can be "community", "degree", or "distance".
    :param skip_frequency_vector:  Whether to skip the frequency vector nodes in the visualization.
    :return:  None
    """
    G = nx.DiGraph()
    add_nodes_edges(G, data, skip_frequency_vector=skip_frequency_vector)

    # Create a Pyvis network
    nt = Network("1000px", "1500px", notebook=True, directed=True)
    nt.from_nx(G)

    if type == "community":
        # Compute the partition with the Louvain method
        partition = community_louvain.best_partition(G.to_undirected())

        # Generate a color palette for each community
        unique_communities = set(partition.values())
        palette = sns.color_palette("hsv", len(unique_communities))
        community_color = {community: mcolors.to_hex(color) for community, color in zip(unique_communities, palette)}

        for node in G.nodes():
            community_id = partition[node]
            hex_color = community_color[community_id]
            nt.get_node(node)['color'] = hex_color
            nt.get_node(node)["title"] = f"Community: {community_id}"
            nt.get_node(node)["value"] = G.degree(node)
            nt.get_node(node)["group"] = community_id

    elif type == "degree":
        degrees = [G.degree(n) for n in G.nodes()]
        max_degree = max(degrees)
        min_degree = min(degrees)
        palette = sns.cubehelix_palette(n_colors=max_degree - min_degree + 1, start=2.8, rot=0.1, light=0.9, dark=0.1)

        degree_color = {node: palette[G.degree(node) - min_degree] for node in G.nodes()}

        for node in G.nodes():
            hex_color = mcolors.to_hex(degree_color[node])
            nt.get_node(node)['color'] = hex_color

        for node in nt.nodes:
            node["title"] = f"Degree: {G.degree(node['id'])}"
            node["value"] = G.degree(node['id'])

    elif type == "distance":
        def find_max_distances_to_leaves(dependency_tree):
            distances = {}

            def traverse(node, path):
                if not node:
                    return 0
                max_depth = -1
                for key, value in node.items():
                    depth = traverse(value, path + [key])
                    max_depth = max(max_depth, depth)
                distances[path[-1]] = max_depth + 1
                return max_depth + 1

            for root_key, subtree in dependency_tree.items():
                traverse(subtree, [root_key])
            return distances

        distances = find_max_distances_to_leaves(data)

        G = nx.DiGraph()

        def add_nodes_edges_distance(graph, data, parent=None):
            if isinstance(data, dict):
                for key, value in data.items():
                    graph.add_node(key, distance=distances.get(key, 0))
                    if parent:
                        graph.add_edge(parent, key)
                    add_nodes_edges_distance(graph, value, key)

        add_nodes_edges_distance(G, data)

        nt = Network("1000px", "1500px", notebook=True, directed=True)
        nt.from_nx(G)

        max_distance = max(distances.values())
        palette = sns.color_palette("YlOrRd", max_distance + 1)

        for node in G.nodes():
            distance = G.nodes[node]['distance']
            color = palette[distance] if distance != 0 else (1, 1, 1)
            hex_color = mcolors.to_hex(color)
            nt.get_node(node)['color'] = hex_color
            nt.get_node(node)["title"] = f"Distance: {distance}"
            nt.get_node(node)["value"] = distance

    # Set options for the network
    nt.set_options("""
    var options = {
      "nodes": {
        "borderWidth": 2,
        "borderWidthSelected": 4,
        "color": {
          "border": "rgba(255,255,255,1)",
          "background": "rgba(0,204,204,1)",
          "highlight": {
            "border": "rgba(255,217,102,1)",
            "background": "rgba(255,230,179,1)"
          }
        },
        "font": {
          "size": 20
        }
      },
      "edges": {
        "color": {
          "color": "rgba(50,50,50,1)",
          "highlight": "rgba(217,255,50,1)",
          "hover": "rgba(200,200,200,1)",
          "inherit": false
        },
        "smooth": {
          "type": "continuous"
        }
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 50,
        "hideEdgesOnDrag": true
      },
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -500000,
          "centralGravity": 10,
          "springLength": 150,
          "springConstant": 0.01,
          "damping": 0.09,
          "avoidOverlap": 0.1
        },
        "minVelocity": 0.75
      }
    }
    """)

    nt.save_graph(file_name_export)


if __name__ == "__main__":
    with open('/home/ronceray/Documents/PLASMAG/PLASMAG/output/tree_spice.json', 'r') as file:
        data = json.load(file)

    create_tree(data, "network_community.html", type="community", skip_frequency_vector=True)
    create_tree(data, "network_degree.html", type="degree", skip_frequency_vector=True)
    create_tree(data, "network_distance.html", type="distance", skip_frequency_vector=True)

    html_file_path = "network_community.html"
    title = "Network Community"
    description = "This is a test description."
    add_title_description(html_file_path, title, description)

    html_file_path = "network_degree.html"
    title = "Network Degree"
    description = "This is a test description."
    add_title_description(html_file_path, title, description)

    html_file_path = "network_distance.html"
    title = "Network Distance"
    description = "This is a test description."

