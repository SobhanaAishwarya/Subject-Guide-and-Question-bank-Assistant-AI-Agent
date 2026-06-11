def retrieve_context(
        vectorstore,
        query,
        k=5
):

    docs = vectorstore.similarity_search(
        query,
        k=k
    )

    context = "\n\n".join(
        doc.page_content
        for doc in docs
    )

    return context