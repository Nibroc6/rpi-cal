import json
import numpy as np
import plotly.express as px
from sentence_transformers import SentenceTransformer
from sklearn.manifold import TSNE
#import chromadb
#from pprint import pprint

# load the sample data
with open('posts.json', 'r') as f:
    events = json.load(f)
    
# Load the pre-trained model
model = SentenceTransformer('all-MiniLM-L6-v2')

# get embeddings per topic
j_embeddings = []
for event in events["events"]:
    m = model.encode(event["event_name"])
    #print(len(m))
    j_embeddings.append([m,event["event_id"]])
    

text = "\n".join(["UPDATE events SET vector_title = '{}' WHERE event_id = {};".format(x[0].tolist(), x[1]) for x in j_embeddings])
with open('data2.txt', 'w', encoding='utf-8') as f:
    f.write(text)
    f.close()
    
j_embeddings = [x[0] for x in j_embeddings]
import json
with open('data2.json', 'w', encoding='utf-8') as f:
    json.dump([x.tolist() for x in j_embeddings], f)
    
"""# combine embeddings in single array
topics = ["apple"]
for topic in topics[2:]:
    embeddings = np.vstack((embeddings, j_embeddings[topic]))
"""    
embeddings = np.vstack(tuple(j_embeddings))

#embeddings = j_embeddings

# Perform TSNE to reduce to 2 components
tsne_model = TSNE(n_components=2, random_state=42)
tsne_embeddings_values = tsne_model.fit_transform(embeddings)
num_elements_per_topic = 51
num_topics = int(embeddings.shape[0]/num_elements_per_topic)
#col_topics = [element for element in topics for _ in range(num_elements_per_topic)]

fig = px.scatter(
    x = tsne_embeddings_values[:,0], 
    y = tsne_embeddings_values[:,1],
)

fig.update_traces(marker=dict(size=13))  # Increase the marker size uniformly


fig.update_layout(
    xaxis=dict(showticklabels=False, title=''),
    yaxis=dict(showticklabels=False, title=''),
    #showlegend=False,
    autosize=False,
    #width=600,  # Width of the plot
    #height=600,  # Height of the plot
    margin=dict(l=50, r=50, b=50, t=50, pad=4)  # Margins
)
fig.show()