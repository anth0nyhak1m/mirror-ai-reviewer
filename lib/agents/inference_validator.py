# inference validator

# %%
"""
inference_validator.py

Validate the inference of a model using the toulmin model of argumentation.
- If the inference is not valid, return the reason why.
- If the inference is valid, return the reason why.
- If the inference is not valid, return the reason why.
"""

# %%


from enum import Enum

from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from lib.config.llm_models import gpt_5_model
from lib.models.agent import DEFAULT_LLM_TIMEOUT, AgentProtocol


class WarrantExpression(str, Enum):
    STATED = "stated"
    IMPLIED = "implied"
    NONE = "none"


class ToulminClaim(BaseModel):
    text: str = Field(
        description="The exact excerpt from the chunk that implies the claim"
    )
    claim: str = Field(
        description="The claim or inferential conclusion made within the excerpt"
    )
    # rationale: str = Field(
    #     description="Why the excerpt implies this claim (brief analytic rationale)"
    # )

    # Toulmin elements
    data: list[str] = Field(
        default_factory=list,
        description=(
            "Data/Grounds: evidence or facts supporting the claim, quoted or paraphrased as taken from the preceding text."
        ),
    )
    warrants: list[str] = Field(
        default_factory=list,
        description=(
            "Warrants: assumptions that connect the data to the claim (may be cultural, logical, or methodological). Follows from the domain context or related references."
        ),
    )
    warrant_expression: WarrantExpression = Field(
        description=(
            "Whether the primary warrant is stated explicitly, implied implicitly, or none could be identified"
        )
    )
    qualifiers: list[str] = Field(
        default_factory=list,
        description=(
            "Qualifiers: words/phrases indicating the strength/scope of the claim (e.g., 'likely', 'some', 'in many cases'). Helps determine if the claim has been overstated or understated."
        ),
    )
    rebuttals: list[str] = Field(
        default_factory=list,
        description=(
            "Rebuttals: acknowledged exceptions, counter-arguments, or conditions under which the claim may not hold. Helps determine if the claim has been overstated or understated."
        ),
    )
    backing: list[str] = Field(
        default_factory=list,
        description=(
            "Backing: additional support that justifies the warrant (e.g., principles, studies, or theoretical reasons). Helps determine if the claim has been overstated or understated."
        ),
    )


class InferenceValidationResponse(BaseModel):
    valid: bool = Field(
        description="Considering the Toulmin elements, whether the inference is valid or not"
    )
    rationale: str = Field(
        description="The rationale for why you think the inference is valid or not. If the inference is not valid, explain why. If the inference is valid, explain why. In only TWO sentences."
    )
    suggested_action: str = Field(
        description="A suggested action to take if the inference is not valid. If the inference is valid, return 'No changes needed'. In only TWO sentences."
    )


class InferenceValidationResponseWithClaimIndex(InferenceValidationResponse):
    claim_index: int = Field(
        description="The index of the claim that is being validated"
    )
    chunk_index: int = Field(
        description="The index of the chunk that contains the claim"
    )


_inference_validation_prompt = ChatPromptTemplate.from_template(
    """
## Task
You are a inference validator using the Toulmin model of argumentation. You will receive the full document (context) and a specific chunk. Validate the inference of the chunk and, when possible, identify Toulmin elements for each claim.

- If a Toulmin element is not present, return an empty list for that element. For the warrant expression, return one of: "stated", "implied", or "none".
- If the chunk of text is a bibliographic entry (usually found in the references or bibliography section of the full document), do not consider it as having claims.
- If the chunk of text does not contain any argumentative content, do not consider it as having claims.

## Toulmin Definitions (concise)
- Claim: the assertion or conclusion to be established and whose validity is being determined.
- Data/Grounds: evidence or facts that support the claim.
- Warrant: the assumption or principle that connects data to claim; it may be stated explicitly or implied implicitly. Follows from the domain context or related references.
- Qualifier: words/phrases indicating the strength/scope of the claim (e.g., "likely", "some", "many", "in most cases").
- Rebuttal: acknowledged exceptions or counter-arguments to the claim.
- Backing: additional support that justifies the warrant (e.g., theories, principles, authorities, or methodological reasons).



## Reference: Purdue OWL - Toulmin Argument (for definitions and orientation)
<begin excerpt>
The Toulmin method is a style of argumentation that breaks arguments down into six component parts: claim, grounds, warrant, qualifier, rebuttal, and backing. In Toulmin’s method, every argument begins with three fundamental parts: the claim, the grounds, and the warrant.

- A claim is the assertion that authors would like to prove to their audience. It is, in other words, the main argument.

- The grounds of an argument are the evidence and facts that help support the claim.

- Finally, the warrant, which is either implied or stated explicitly, is the assumption that links the grounds to the claim.

For example, if you argue that there are dogs nearby, because you hear them barking, the claim is "there are dogs nearby", the grounds are "you hear barking and howling", and the warrant is "dogs are animals that bark and howl".

In this example, in order to assert the claim that a dog is nearby, we provide evidence and specific facts—or the grounds—by acknowledging that we hear barking and howling. Since we know that dogs bark and howl (i.e., since we have a warrant) we can assume that a dog is nearby.

Now, let's try a more academic approach. Let's say that you are writing a paper on how more research needs to be done on the way that computer-mediated communication influences online and offline relationships.

Let the claim be "Additional research needs on computer-mediated communication needs to be conducted to better understand how online interactions affect relationships". The grounds are "In their paper, Cummings et al. discuss how email communications are an inferior means of maintaining personal relationships. However, their study does not account for technological, demographic, or modality limitations." The warrant is "When a paper lacks a certain perspective, more research would be beneficial to prove its claims."

In this case, to assert the claim that additional research needs to be made on how online communication affects relationships, the author shows how the original article needs to account for technological, demographic, and modality limitations in the study.  Since we know that when a study lacks a perspective, it would be beneficial to do more research (i.e., we have a warrant), it would be safe to assume that more research should be conducted (i.e. the claim).

The other three elements—backing, qualifier, and rebuttal—are not fundamental to a Toulmin argument, but may be added as necessary. Using these elements wisely can help writers construct full, nuanced arguments.

- Backing refers to any additional support of the warrant. In many cases, the warrant is implied, and therefore the backing provides support for the warrant by giving a specific example that justifies the warrant.

- The qualifier shows that a claim may not be true in all circumstances. Words like “presumably,” “some,” and “many” help your audience understand that you know there are instances where your claim may not be correct.

- Rebuttal is an acknowledgement of another valid view of the situation.

Including a qualifier or a rebuttal in an argument helps build your ethos, or credibility. When you acknowledge that your view isn’t always true or when you provide multiple views of a situation, you build an image of a careful, unbiased thinker, rather than of someone blindly pushing for a single interpretation of the situation.

In the dog example, a backing could be that "You know that your neighbor Tom has two large German Shepherds," and a qualifier could be that "Tom's dogs are likely at home," a rebuttal could be that "There is a child at home that likes watching shows about dogs."

In the academic paper example, a backing could be "A thorough review of the literature has shown that no further research has been done to clarify the effects of computer mediated communications on personal relationships," a qualifier could be "likely", and a rebuttal could be "There might be research on the topic that has yet to be published."

<End Excertp>

## Important Instructions
- Focus only on content in the provided chunk when validating the inference; use the full document only for context/clarification.
- Validate the inference of the chunk. If the inference is not valid, return an empty list.
- For the identified claim, specify the following Toulmin elements:
  - "data": list specific evidence from the chunk that supports the claim (quoted or paraphrased).
  - "warrants": list the assumptions that link the data to the claim. If you infer a warrant from context, include it.
  - "warrant_expression": the expression of the warrant as "stated", "implied", or "none".
  - "backing": list any additional support for the warrant (e.g., principles, cited studies, theoretical reasons) if present. Helps determine if the claim has been overstated or understated.
  - "qualifiers": list hedging or scope-limiting language contained within the claim.
  - "rebuttals": list acknowledged exceptions or counter-arguments only if they are present in the chunk. The lack of rebuttals does not reduce the validity of the claim but the existence of rebutalls can bolster a claim by acknowledging that it is not an absolute statement.
- In only TWO sentences, explain why you think the inference is valid or not.
- In only TWO sentences, suggest an action to take if the inference is not valid. If the inference is valid, return 'No changes needed'.

## Domain context of the document (i.e., the subject area the document falls in)
{domain_context}

## Audience context of the document (i.e., the intended audience for the document)
{audience_context}

## The full document that the chunk is a part of
```
{full_document}
```

## The paragraph of the original document that contains the chunk of text that we want to analyze
```
{paragraph}
```

## The chunk of text to analyze
```
{chunk}
```

## The claim to validate
```
{claim}
```
"""
)


class InferenceValidatorAgent(AgentProtocol):
    name = "Inference Validator"
    description = (
        "Validate the inference of a model using the toulmin model of argumentation."
    )

    def __init__(self):
        self.llm = init_chat_model(
            gpt_5_model.model_name,
            temperature=0.2,
            timeout=DEFAULT_LLM_TIMEOUT,
        ).with_structured_output(InferenceValidationResponse)

    async def ainvoke(
        self,
        prompt_kwargs: dict,
        config: RunnableConfig = None,
    ) -> InferenceValidationResponse:
        messages = _inference_validation_prompt.format_messages(**prompt_kwargs)
        return await self.llm.ainvoke(messages, config=config)


inference_validator_agent = InferenceValidatorAgent()


# %%


if __name__ == "__main__":
    import nest_asyncio
    import asyncio

    nest_asyncio.apply()

    # Test code
    async def test_inference_validator():
        """Test the inference validator with sample data"""

        # Sample test data; now includes explicit claim_index and chunk_index for withClaimIndex structure
        test_data = {
            "full_document": """
            Renewable energy capacity has grown significantly in recent years.
            Solar and wind power installations have increased by 40% since 2020.
            This growth is driven by declining costs and supportive government policies.
            However, challenges remain in grid integration and energy storage.
            """,
            "paragraph": """
            Solar and wind power installations have increased by 40% since 2020.
            This growth is driven by declining costs and supportive government policies.
            """,
            "chunk": "Solar and wind power installations have increased by 40% since 2020.",
            "claim": "Renewable energy capacity is expanding rapidly",
            "domain_context": "This is a report on energy infrastructure trends.",
            "audience_context": "The intended audience is policymakers and energy sector analysts.",
            "claim_index": 0,
            "chunk_index": 0,
        }

        # Create agent instance
        agent = InferenceValidatorAgent()

        # Test the validation
        print("Testing Inference Validator Agent")
        print("=" * 80)
        print(f"Claim: {test_data['claim']}")
        print(f"Chunk: {test_data['chunk']}")
        print("\nValidating...\n")

        result = await agent.ainvoke(test_data)

        print("Results:")
        print("-" * 80)
        print(f"Valid: {result.valid}")
        print(f"\nRationale:\n{result.rationale}")
        print(f"\nSuggested Action:\n{result.suggested_action}")
        print(f"Claim Index: {result.claim_index}")
        print(f"Chunk Index: {result.chunk_index}")
        print("=" * 80)

        return result

    async def test_invalid_inference():
        """Test with an invalid inference to see how the validator handles it"""

        test_data = {
            "full_document": """
            Solar panel efficiency has improved by 15% over the last decade.
            Manufacturing costs have decreased due to economies of scale.
            """,
            "paragraph": "Solar panel efficiency has improved by 15% over the last decade.",
            "chunk": "Solar panel efficiency has improved by 15% over the last decade.",
            "claim": "Solar panels will replace all fossil fuel energy by 2030",
            "domain_context": "This is a report on solar technology improvements.",
            "audience_context": "The intended audience is technology investors.",
            "claim_index": 0,
            "chunk_index": 0,
        }

        agent = InferenceValidatorAgent()

        print("\nTesting Invalid Inference")
        print("=" * 80)
        print(f"Claim: {test_data['claim']}")
        print(f"Chunk: {test_data['chunk']}")
        print("\nValidating...\n")

        result = await agent.ainvoke(test_data)

        print("Results:")
        print("-" * 80)
        print(f"Valid: {result.valid}")
        print(f"\nRationale:\n{result.rationale}")
        print(f"\nSuggested Action:\n{result.suggested_action}")
        print(f"Claim Index: {result.claim_index}")
        print(f"Chunk Index: {result.chunk_index}")
        print("=" * 80)

        return result

    print("\n🔍 Running Inference Validator Tests\n")

    # Run valid inference test
    result = asyncio.run(test_inference_validator())
    print("Valid Inference Test Result:")
    print(result.model_dump_json(indent=2))

    # Run invalid inference test
    result = asyncio.run(test_invalid_inference())
    print("Invalid Inference Test Result:")
    print(result.model_dump_json(indent=2))
