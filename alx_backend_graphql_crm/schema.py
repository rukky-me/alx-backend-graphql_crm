import graphene

#this creates a query class
class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello, GraphQL!")

#this creates the Graphql schema
schema = graphene.Schema(query=Query)
