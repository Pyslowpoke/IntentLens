import json
import httpx
import pytest
from services.api.providers import ProviderAdapter

RESULT={'proposals':[{'title':'A','explanation':'one','plan':{'aggregation':'count'},'spec':{}},{'title':'B','explanation':'two','plan':{'aggregation':'count'},'spec':{}}]}

@pytest.mark.parametrize('provider',['openai','deepseek','anthropic','ollama'])
def test_protocol(provider):
    def handle(request):
        body=json.loads(request.content)
        assert body['model']=='fixture-model'
        if provider in ('openai','deepseek'):
            assert request.url.path=='/v1/chat/completions'
            assert request.headers['authorization']=='Bearer fixture-key'
            assert body['response_format']=={'type':'json_object'}
            return httpx.Response(200,json={'choices':[{'message':{'content':json.dumps(RESULT)}}]})
        if provider=='anthropic':
            assert request.url.path=='/v1/messages'
            assert request.headers['x-api-key']=='fixture-key'
            assert request.headers['anthropic-version']=='2023-06-01'
            assert 'system' in body and body['messages'][0]['role']=='user'
            return httpx.Response(200,json={'content':[{'type':'text','text':json.dumps(RESULT)}]})
        assert request.url.path=='/api/chat'
        assert body['stream'] is False and 'properties' in body['format']
        return httpx.Response(200,json={'message':{'content':json.dumps(RESULT)}})
    base='http://fixture'+('' if provider=='ollama' else '/v1')
    result=ProviderAdapter(provider,base,'fixture-model','fixture-key',httpx.MockTransport(handle)).request('goal')
    assert len(result.proposals)==2

@pytest.mark.parametrize('provider',['openai','deepseek','anthropic','ollama'])
@pytest.mark.parametrize('status,match',[(401,'authentication'),(429,'rate limit'),(500,'HTTP 500')])
def test_error_redaction(provider,status,match):
    adapter=ProviderAdapter(provider,'http://fixture','fixture-model','super-secret',httpx.MockTransport(lambda r:httpx.Response(status,json={'secret':'super-secret'})))
    with pytest.raises(ValueError,match=match) as e:adapter.request('test')
    assert 'super-secret' not in str(e.value)
